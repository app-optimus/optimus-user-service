from http import HTTPStatus

from app.enums import Tables
from app.utils import create_query_params, generate_nano_id, create_insert_query_with_values


class EntityCreation:

    def __init__(self, db=None, logger=None, x_user=None):
        self.db = db
        self.logger = logger
        self.x_user = x_user

    entity_detail_columns = [
        "entity_id", "name", "code", "address", "city", "state", "zip_code", "country", "head_name", "head_email",
        "selected_features", "created_by", "updated_by",
    ]

    async def check_entity_exist(self, entity_name, entity_code):
        _columns = ["1"]
        where_dict = {
            f"(entity_name = '{entity_name}' OR entity_code = '{entity_code}')%s": "",
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
        status, message, status_code = self.check_entity_exist(payload.get("name"), payload.get("code"))
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
            "selected_features": selected_features
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

