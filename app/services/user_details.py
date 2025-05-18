from http import HTTPStatus

import shortuuid

from app.enums import Tables
from app.services.permissions import EntityPermissions
from app.utils import create_query_params, create_insert_query_with_values, execute_transactional_queries, \
    create_update_query_with_values, get_default_password, generate_salt, get_passkey, generate_nano_id


class UserCreation:

    def __init__(self, db=None, logger=None, x_user=None):
        self.db = db
        self.logger = logger
        self.x_user = x_user

    core_user_detail_columns = ["user_id", "user_name", "user_email", "user_code", "created_by", "updated_by"]
    user_entity_detail_columns = ["entity_id", "user_id", "user_role", "permission_id", "created_by", "updated_by"]
    core_global_user_columns = ["user_id", "user_name", "user_email", "created_by", "updated_by", "is_chief_admin"]

    async def create_global_user(self, payload: dict):
        success, user_details = await self.validate_user_already_exist(
            payload.get("user_email")
        )
        if not success:
            return False, "Failed to fetch existing user details", HTTPStatus.OK.value, {}

        if user_details["user_id"]:
            return False, "User with the provided email already exist", HTTPStatus.BAD_REQUEST, {}

        user_id = generate_nano_id(length=10)
        default_password = get_default_password(payload["user_name"])
        salt = generate_salt()
        passkey = get_passkey(default_password, salt)
        payload.update({
            "user_id": user_id,
            "created_by": self.x_user["user_id"],
            "updated_by": self.x_user["user_id"],
            "is_chief_admin": True
        })

        core_global_user_details = dict()
        for column in self.core_global_user_columns:
            core_global_user_details[column] = payload[column]

        core_user_query, core_user_details = create_insert_query_with_values(
            table=Tables.user_details, insert_data=core_global_user_details
        )
        user_credentials_query, credential_details = create_insert_query_with_values(
            table=Tables.user_authentication,
            insert_data={
                "user_id": user_id,
                "user_passkey": passkey,
                "salt": salt
            }
        )

        queries = [
            (core_user_query, core_user_details),
            (user_credentials_query, credential_details)
        ]

        try:
            await execute_transactional_queries(db=self.db, queries=queries)
        except Exception as e:
            self.logger.error(f"failed to execute transactional query due to {e}")
            return False, "Failed to to create user", HTTPStatus.INTERNAL_SERVER_ERROR, {}

        return True, "Successfully created user", HTTPStatus.OK, {"user_id": user_id}

    async def create_entity_user(self, payload: dict):
        success, user_details = await self.validate_user_already_exist(
            payload.get("user_email")
        )
        if not success:
            return False, "Failed to fetch existing user details", HTTPStatus.OK.value, {}

        if user_details["is_active"]:
            return False, "User with the provided email already exist", HTTPStatus.BAD_REQUEST, {}

        filters = {"permission_name": payload["permission_name"]}
        status, _, _, permission_data = await EntityPermissions(db=self.db, logger=self.logger).fetch_entity_permissions(
            payload["entity_id"], filters=filters
        )
        if not status:
            return False, "failed to fetch permission details", HTTPStatus.INTERNAL_SERVER_ERROR, {}

        if not permission_data:
            return False, "permission name provided doesn't exist", HTTPStatus.BAD_REQUEST, {}

        permission_id = list(permission_data.keys())[0]
        payload.update({
            "permission_id": permission_id,
            "created_by": self.x_user["user_id"],
            "updated_by": self.x_user["user_id"]
        })

        if user_details.get("user_id"):
            success, message, status_code, data = await self.update_existing_user_data(
                user_details["user_id"], payload
            )
        else:
            success, message, status_code, data = await self.insert_user_details(payload)

        return success, message, status_code, data

    async def update_existing_user_data(self, user_id, payload):
        core_user_columns = ["user_name", "user_code", "updated_by", "active", "is_deleted"]
        payload.update({"active": True, "is_deleted": False})
        core_user_details, entity_user_details = dict(), dict()
        for column in core_user_columns:
            core_user_details[column] = payload[column]

        for column in self.user_entity_detail_columns:
            entity_user_details[column] = payload[column]

        core_user_query, core_user_details = create_update_query_with_values(
            Tables.user_details, core_user_details, {"user_id": user_id}
        )
        entity_user_query, entity_user_details = create_insert_query_with_values(
            table=Tables.user_entity_details, insert_data=entity_user_details
        )

        queries = [(core_user_query, core_user_details), (entity_user_query, entity_user_details)]
        try:
            await execute_transactional_queries(db=self.db, queries=queries)
        except Exception as e:
            self.logger.error(f"failed to execute transactional query due to {e}")
            return False, "Failed to to create user", HTTPStatus.INTERNAL_SERVER_ERROR, {}

        return True, "Successfully created user", HTTPStatus.OK, {"user_id": user_id}

    async def insert_user_details(self, payload):
        user_id = generate_nano_id(length=10)
        default_password = get_default_password(payload["user_name"])
        salt = generate_salt()
        passkey = get_passkey(default_password, salt)
        payload.update({"user_id": user_id})

        core_user_details, entity_user_details = dict(), dict()
        for column in self.core_user_detail_columns:
            core_user_details[column] = payload[column]

        for column in self.user_entity_detail_columns:
            entity_user_details[column] = payload[column]

        core_user_query, core_user_details = create_insert_query_with_values(
            table=Tables.user_details, insert_data=core_user_details
        )
        entity_user_query, entity_user_details = create_insert_query_with_values(
            table=Tables.user_entity_details, insert_data=entity_user_details
        )
        user_credentials_query, credential_details = create_insert_query_with_values(
            table=Tables.user_authentication,
            insert_data={
                "user_id": user_id,
                "user_passkey": passkey,
                "salt": salt
            }
        )

        queries = [
            (core_user_query, core_user_details),
            (entity_user_query, entity_user_details),
            (user_credentials_query, credential_details)
        ]

        try:
            await execute_transactional_queries(db=self.db, queries=queries)
        except Exception as e:
            self.logger.error(f"failed to execute transactional query due to {e}")
            return False, "Failed to to create user", HTTPStatus.INTERNAL_SERVER_ERROR, {}

        return True, "Successfully created user", HTTPStatus.OK, {"user_id": user_id}

    async def validate_user_already_exist(self, user_email):
        _columns = ["ud.user_id", "ud.active", "ud.user_code"]
        where_dict = {
            "user_email = '%s'": user_email
        }

        _columns, _where = create_query_params(_columns, where_dict)
        query = f"""SELECT {_columns} FROM {Tables.user_details} ud WHERE {_where};"""

        try:
            response = await self.db.fetch_all(query)
        except Exception as e:
            self.logger.error(f"failed to fetch user details due to {e}")
            return False, {}

        user_details = {
            "is_active": False,
            "user_id": None,
            "user_code": None
        }

        if response:
            user_details["user_id"] = response[0]["user_id"]
            user_details["is_active"] = response[0]["active"]
            user_details["user_code"] = response[0]["user_code"]

        return True, user_details


class UserDetails:

    def __init__(self, db=None, logger=None):
        self.db = db
        self.logger = logger

    async def fetch_user_details(self, user_id: str = None, core_filters: dict = None):
        columns = ["user_id", "user_name", "is_chief_admin"]
        _where = {f"{key} = '%s'": value for key, value in core_filters.items()}
        _where["active = %s"] = True
        if user_id:
            _where["user_id = '%s'"] = user_id
        _columns, _where = create_query_params(columns, core_filters)

        query = f"""SELECT {_columns} from {Tables.user_details} WHERE {_where};"""

        try:
            response = await self.db.fetch_one(query)
        except Exception as e:
            self.logger.error(f"failed to fetch authentication details due to {e}")
            return False, "failed to fetch authentication details", HTTPStatus.INTERNAL_SERVER_ERROR, {}

        data = {key: response[key] for key in columns}

        return True, "successfully fetched used details", HTTPStatus.OK, data
