import json
from http import HTTPStatus

from pymysql import IntegrityError

from app.enums import Tables
from app.utils import create_query_params, generate_nano_id, create_insert_query_with_values, is_unique_violation


class EntityPermissions:

    def __init__(self, db=None, logger=None, x_user=None):
        self.db = db
        self.logger = logger
        self.x_user = x_user

    async def fetch_entity_permissions(self, entity_id: str, filters: dict = {}):
        _columns = ["permission_id", "permission_json", "permission_name"]
        _where = {
            "entity_id = '%s'": entity_id,
            "active = %s": True
        }
        for key, value in filters.items():
            _where[f"{key} = '%s'"] = value

        _columns, _where = create_query_params(columns=_columns, where_dict=_where)
        query = f"SELECT {_columns} FROM {Tables.entity_permissions} WHERE {_where};"
        try:
            response = await self.db.fetch_all(query)
        except Exception as e:
            self.logger.error(f"failed to fetch entity permissions due to {e}")
            return False, "Failed to fetch entity permissions", HTTPStatus.INTERNAL_SERVER_ERROR, {}

        data = dict()
        for detail in response:
            permission_id = detail["permission_id"]
            permission_json = json.loads(detail["permission_json"])
            data[permission_id] = {
                "permission_id": permission_id,
                "permission_name": detail["permission_name"],
                "permission_json": permission_json
            }

        return True, "successfully fetched permissions", HTTPStatus.OK, data

    async def create_entity_permission(self, entity_id: str, permission_name: str, permission_json: dict):
        permission_id = generate_nano_id(length=8)
        insert_values = {
            "entity_id": entity_id,
            "permission_id": permission_id,
            "permission_name": permission_name,
            "permission_json": json.dumps(permission_json),
            "created_by": self.x_user["user_id"],
            "updated_by": self.x_user["user_id"]
        }

        query, values = create_insert_query_with_values(Tables.entity_permissions, insert_values)
        try:
            await self.db.execute(query=query, values=values)
        except IntegrityError:
            return False, "Permission with same name already exist", HTTPStatus.BAD_REQUEST
        except Exception as e:
            self.logger.error(f"failed to insert data in table due to {e}")
            return False, "Failed to create permission", HTTPStatus.INTERNAL_SERVER_ERROR

        return True, "Successfully created permission", HTTPStatus.CREATED
