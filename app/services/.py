import json
from http import HTTPStatus

from app.enums import Tables
from app.utils import create_query_params, generate_nano_id, create_insert_query_with_values


class EntityService:

    def __init__(self, db=None, logger=None, x_user=None):
        self.db = db
        self.logger = logger
        self.x_user = x_user

    entity_detail_columns = [
        "entity_id", "name", "code", "address", "city", "state", "zip_code", "country", "head_name", "head_email",
        "selected_features", "created_by", "updated_by",
    ]

    async def fetch_entities(self):
        _columns = ["entity_id", "name", "code", "city", "state", "head_name", "head_email"]
        _where = {"active = %s": True}
        _columns, _where = create_query_params(columns=_columns, where_dict=_where)
        query = f"SELECT {_columns} FROM {Tables.entity_details} WHERE {_where};"

        try:
            response = await self.db.fetch_all(query)
        except Exception as e:
            self.logger.error(f"failed to fetch entities due to {e}")
            return False, "Failed to fetch entities", HTTPStatus.INTERNAL_SERVER_ERROR, []

        data = [dict(row) for row in response]
        return True, "Successfully fetched entities", HTTPStatus.OK, data

    async def check_entity_exist(self, entity_name, entity_code):
        _columns = ["1"]
        where_dict = {
            f"(name = '{entity_name}' OR code = '{entity_code}')%s": "",
            "active = %s": True
        }

        _columns, _where = create_query_params(_columns, where_dict)
        query = f"""SELECT {_columns} FROM {Tables.entity_details} ud WHERE {_where};"""

        try:
            response = await self.db.fetch_all(query)
        except Exception as e:
            self.logger.error(f"failed to fetch entity details due to {e}")
            return False, "Failed to fetch entity details", HTTPStatus.INTERNAL_SERVER_ERROR

        return False if response else True, "Entity with provided name or code already exists", HTTPStatus.BAD_REQUEST

    async def create_entity(self, payload):
        status, message, status_code = await self.check_entity_exist(payload.get("name"), payload.get("code"))
        if not status:
            return False, message, status_code

        entity_id = generate_nano_id(length=12)
        selected_features = payload.pop("selected_features", None)
        if selected_features:
            selected_features = {feature: True for feature in selected_features}

        payload.update({
            "entity_id": entity_id,
            "created_by": self.x_user["user_id"],
            "updated_by": self.x_user["user_id"],
            "selected_features": json.dumps(selected_features) if selected_features else None
        })

        entity_query, entity_details = create_insert_query_with_values(
            table=Tables.entity_details, insert_data=payload
        )

        try:
            await self.db.execute(query=entity_query, values=entity_details)
        except Exception as e:
            self.logger.error(f"failed to insert data in table due to {e}")
            return False, "Failed to create entity", HTTPStatus.INTERNAL_SERVER_ERROR

        return True, "Successfully created entity", HTTPStatus.CREATED

