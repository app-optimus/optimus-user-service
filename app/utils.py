import logging
from hashlib import sha256

import nanoid
from base64 import b64encode

from os import urandom
from typing import Tuple, List
from uuid import UUID

from databases import Database
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pymysql import IntegrityError

from app.enums import Tables

logger = logging.getLogger(__name__)


def standard_response_generator(
    success, message, http_status, data={}
):
    logger.info("API RESPONSE")
    response = {
        "success": success,
        "message": message,
        "data": data,
    }
    json_compatible_response = jsonable_encoder(response)
    api_response = JSONResponse(status_code=http_status, content=json_compatible_response)
    logger.info(f"RESPONSE_STATUS_CODE : {api_response.status_code}")
    logger.info(f"RESPONSE_DATA : {response}")
    logger.info(f"RESPONSE_HEADERS : {api_response.headers}")
    return api_response


def create_insert_query_with_values(table: Tables, insert_data: dict) -> Tuple[str, dict]:
    columns = ", ".join(list(insert_data.keys()))
    columns_alias = ", ".join(f":{key}" for key in insert_data.keys())
    query = f"INSERT INTO {table} ({columns}) VALUES ({columns_alias});"
    return query, insert_data


def create_update_query_with_values(table: Tables, update_data: dict, where_condition: dict) -> Tuple[str, dict]:
    set_clause = ", ".join(f"{key} = :{key}" for key in update_data.keys())
    where_clause = " AND ".join(f"{key} = :{key}" for key in where_condition.keys())
    query = f"UPDATE {table} SET {set_clause} WHERE {where_clause};"
    values = {**update_data, **where_condition}
    return query, values


def create_query_params(columns: list = None, where_dict: dict = None):
    where = ""
    if columns:
        columns = create_column_query(columns)
    if where_dict:
        where = create_where_condition(where_dict)

    return columns, where


def create_where_condition(where_dict: dict):
    where_condition = " AND ".join(list(where_dict.keys()))
    where_condition = where_condition % tuple(where_dict.values())
    return where_condition


def create_column_query(columns: list):
    return ", ".join(columns)


async def execute_transactional_queries(db: Database, queries: List[Tuple[str, dict]]):
    async with db.transaction():
        for query_data in queries:
            await db.execute(query=query_data[0], values=query_data[1])


def _is_valid_uuid(val):
    try:
        UUID(str(val))
        return True
    except ValueError:
        return False


def generate_salt():
    return b64encode(urandom(10)).decode("utf-8")


def get_default_password(user_name: str) -> str:
    """
    Generate default password for a new user
    """
    return f"{user_name.replace(' ', '')}@1234"
    # return generate_nano_id(length=8) + "@!"


def generate_nano_id(length: int = 16) -> str:
    """
    Generate an alphanumeric nanoid of provided length
    """
    return nanoid.generate("1234567890abcdefghijklmnopqrstuvwxyz", length)


def get_passkey(password: str, salt: str):
    return sha256(bytes("{}{}".format(password, salt), encoding="utf-8")).hexdigest()


def is_unique_violation(exc: Exception) -> bool:
    if isinstance(exc, IntegrityError):
        orig = getattr(exc, "orig", None)
        if orig and hasattr(orig, "args") and len(orig.args) > 0:
            if orig.args[0] == 1062:
                return True
    return False
