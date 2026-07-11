import asyncio
from http import HTTPStatus
from io import BytesIO
import pandas as pd

from app.constants import BULK_USER_CREATION_MAX_SIZE
from app.enums import Tables, UserRoles
from app.services.permissions import EntityPermissions
from app.utils import create_query_params, create_insert_query_with_values, execute_transactional_queries, \
    create_update_query_with_values, get_default_password, generate_salt, get_passkey, generate_nano_id, \
    where_clause_for_multiple


class UserCreation:

    def __init__(self, db=None, logger=None, x_user=None):
        self.db = db
        self.logger = logger
        self.x_user = x_user

    core_user_detail_columns = ["user_id", "user_name", "user_email", "opti_code", "created_by", "updated_by"]
    user_entity_detail_columns = ["entity_id", "user_id", "user_role", "permission_id", "created_by", "updated_by"]
    student_entity_detail_columns = ["class_id", "section_id", "roll_number", "admission_number"]
    core_global_user_columns = ["user_id", "user_name", "user_email", "created_by", "updated_by", "is_chief_admin"]
    bulk_user_creation_headers = {
        "user_name", "user_email", "permission_id", "roll_number", "admission_number"
    }

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
        status, _, _, permission_data = await EntityPermissions(
            db=self.db, logger=self.logger, x_user=self.x_user
        ).fetch_entity_permissions(payload["entity_id"], filters=filters)
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

        if payload.get("user_role") == UserRoles.student.value:
            success, message, status_code = await self.validate_roll_numbers(
                payload["entity_id"], payload["class_id"], payload["section_id"], [payload["roll_number"]]
            )
            if not success:
                return False, message, status_code, {}

            success, message, status_code = await self.validate_admission_numbers(
                payload["entity_id"], [payload["admission_number"]]
            )
            if not success:
                return False, message, status_code, {}

        if user_details.get("user_id"):
            success, message, status_code, data = await self.update_existing_user_data(
                user_details["user_id"], payload
            )
        else:
            success, message, status_code, data = await self.insert_user_details(payload)

        return success, message, status_code, data

    async def update_user_details(self, payload: dict):
        user_id = payload["user_id"]
        entity_id = payload["entity_id"]
        updated_by = self.x_user["user_id"]

        queries = []

        core_update_data = {}
        if "user_name" in payload:
            core_update_data["user_name"] = payload["user_name"]
        if "user_email" in payload:
            core_update_data["user_email"] = payload["user_email"]

        if core_update_data:
            core_update_data["updated_by"] = updated_by
            core_query, core_values = create_update_query_with_values(
                Tables.user_details, core_update_data, {"user_id": user_id}
            )
            queries.append((core_query, core_values))

        entity_update_data = {}
        if "user_role" in payload:
            entity_update_data["user_role"] = payload["user_role"]

        if "permission_name" in payload:
            filters = {"permission_name": payload["permission_name"]}
            status, _, _, permission_data = await EntityPermissions(
                db=self.db, logger=self.logger, x_user=self.x_user
            ).fetch_entity_permissions(entity_id, filters=filters)
            if not status:
                return False, "Failed to fetch permission details", HTTPStatus.INTERNAL_SERVER_ERROR, {}
            if not permission_data:
                return False, "Permission name provided doesn't exist", HTTPStatus.BAD_REQUEST, {}
            entity_update_data["permission_id"] = list(permission_data.keys())[0]

        if entity_update_data:
            entity_update_data["updated_by"] = updated_by
            entity_query, entity_values = create_update_query_with_values(
                Tables.user_entity_details, entity_update_data, {"user_id": user_id, "entity_id": entity_id}
            )
            queries.append((entity_query, entity_values))

        try:
            await execute_transactional_queries(db=self.db, queries=queries)
        except Exception as e:
            self.logger.error(f"failed to execute update query due to {e}")
            return False, "Failed to update user details", HTTPStatus.INTERNAL_SERVER_ERROR, {}

        return True, "Successfully updated user details", HTTPStatus.OK, {"user_id": user_id}

    async def update_existing_user_data(self, user_id, payload):
        core_user_columns = ["user_name", "updated_by", "active", "is_deleted"]
        payload.update({"active": True, "is_deleted": False})
        core_user_details, entity_user_details = dict(), dict()
        for column in core_user_columns:
            core_user_details[column] = payload[column]

        for column in self.user_entity_detail_columns:
            entity_user_details[column] = payload[column]

        if payload.get("user_role") == UserRoles.student.value:
            for column in self.student_entity_detail_columns:
                if payload.get(column) is not None:
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

        if payload.get("user_role") == UserRoles.student.value:
            for column in self.student_entity_detail_columns:
                if payload.get(column) is not None:
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
        _columns = ["ud.user_id", "ud.active", "ud.opti_code"]
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
            "opti_code": None
        }

        if response:
            user_details["user_id"] = response[0]["user_id"]
            user_details["is_active"] = response[0]["active"]
            user_details["opti_code"] = response[0]["opti_code"]

        return True, user_details

    async def process_bulk_user_creation(self, entity_id, class_id, section_id, file_content):
        # file content headers
        # user_name | user_email | permission_id | roll_number | admission_number
        excel_data = pd.read_excel(BytesIO(file_content), engine="openpyxl")
        headers = set(list(excel_data.columns))

        if headers != self.bulk_user_creation_headers:
            return False, "Invalid headers provided in file", HTTPStatus.BAD_REQUEST

        user_data = excel_data.to_dict(orient='records')
        if len(user_data) > BULK_USER_CREATION_MAX_SIZE:
            return False, f"Maximum {BULK_USER_CREATION_MAX_SIZE} can be created at a time", HTTPStatus.FORBIDDEN

        permission_ids, user_emails, roll_numbers, admission_numbers = set(), set(), set(), set()

        for data in user_data:
            if not all([data[key] for key in self.bulk_user_creation_headers]):
                return False, f"Please provide values for {data['user_email']}", HTTPStatus.BAD_REQUEST

            admission_numbers.add(data.get('admission_number'))
            permission_ids.add(data.get('permission_id'))
            roll_numbers.add(data.get('roll_number'))

        if len(user_data) != len(admission_numbers):
            return False, "Duplicate admission numbers provided", HTTPStatus.BAD_REQUEST

        if len(user_data) != len(roll_numbers):
            return False, "Duplicate roll numbers provided", HTTPStatus.BAD_REQUEST

        permission_validation, admission_number_validation, roll_number_validation = await asyncio.gather(
            self.validate_permission_ids(entity_id, list(permission_ids)),
            self.validate_admission_numbers(entity_id, list(admission_numbers)),
            self.validate_roll_numbers(entity_id, class_id, section_id, list(roll_numbers))
        )

        if not permission_validation[0]:
            return False, permission_validation[1], permission_validation[2]

        if not admission_number_validation[0]:
            return False, admission_number_validation[1], admission_number_validation[2]

        if not roll_number_validation[0]:
            return False, roll_number_validation[1], roll_number_validation[2]

        status, message, status_code = await self.execute_bulk_user_creation_queries(
            entity_id, class_id, section_id, user_data
        )
        return status, message, status_code

    async def execute_bulk_user_creation_queries(
        self, entity_id, class_id, section_id, user_data, user_role=UserRoles.student.value
    ):
        # Note: %s here is substituted with an already-parenthesized,
        # comma-joined list of row tuples (e.g. "('a','b'),('c','d')"), so
        # the VALUES clause must NOT wrap it in another pair of parens.
        user_query = f"INSERT INTO {Tables.user_details} (user_id, user_name, user_email) VALUES %s;"
        user_entity_query = (f"INSERT INTO {Tables.user_entity_details} (entity_id, user_id, user_role, "
                             f"permission_id, admission_number, class_id, section_id, roll_number) VALUES %s;")
        authentication_query = f"INSERT INTO {Tables.user_authentication} (user_id, user_passkey, salt) VALUES %s;"

        base_values, user_entity_values, auth_values = list(), list(), list()

        for data in user_data:
            user_id = generate_nano_id(length=10)
            default_password = get_default_password(data["user_name"])
            salt = generate_salt()
            passkey = get_passkey(default_password, salt)

            base_values.append(f"('{user_id}', '{data['user_name']}', '{data['user_email']}')")
            user_entity_values.append(f"('{entity_id}', '{user_id}', '{user_role}', '{data['permission_id']}', "
                                      f"'{data['admission_number']}', '{class_id}', '{section_id}', "
                                      f"'{data['roll_number']}')")
            auth_values.append(f"('{user_id}', '{passkey}', '{salt}')")

        queries = [
            (user_query % (','.join(base_values)), None),
            (user_entity_query % (','.join(user_entity_values)), None),
            (authentication_query % (','.join(auth_values)), None),
        ]

        try:
            await execute_transactional_queries(db=self.db, queries=queries)
        except Exception as e:
            self.logger.error(f"failed to execute insert queries due to {e}")
            return False, "Failed to create users", HTTPStatus.INTERNAL_SERVER_ERROR

        return True, "Successfully created users", HTTPStatus.OK

    async def validate_permission_ids(self, entity_id: str, permission_ids: list):
        _columns = ["permission_id"]
        _where = {
            "entity_id = '%s'": entity_id,
            "active = %s": True,
            where_clause_for_multiple('permission_id', permission_ids): ""
        }
        _columns, _where = create_query_params(columns=_columns, where_dict=_where)
        query = f"SELECT {_columns} FROM {Tables.entity_permissions} WHERE {_where};"
        try:
            response = await self.db.fetch_all(query)
        except Exception as e:
            self.logger.error(f"failed to fetch entity permissions due to {e}")
            return False, "Failed to fetch entity permissions", HTTPStatus.INTERNAL_SERVER_ERROR

        if len(response) != len(permission_ids):
            return False, "Some of the permissions provided doesn't exist", HTTPStatus.BAD_REQUEST

        return True, "success", HTTPStatus.OK

    async def validate_roll_numbers(self, entity_id, class_id, section_id, roll_numbers):
        _columns = ["count(1) as count"]
        _where = {
            "entity_id = '%s'": entity_id,
            "class_id = '%s'": class_id,
            "section_id = '%s'": section_id,
            where_clause_for_multiple('roll_number', roll_numbers): "",
            "active = %s": True
        }
        _columns, _where = create_query_params(columns=_columns, where_dict=_where)
        query = f"SELECT {_columns} FROM {Tables.user_entity_details} WHERE {_where};"
        try:
            response = await self.db.fetch_all(query)
        except Exception as e:
            self.logger.error(f"failed to fetch user entity class data due to {e}")
            return False, "Failed to fetch user class details", HTTPStatus.INTERNAL_SERVER_ERROR

        if response and response[0]["count"] > 0:
            return False, "Some of the roll numbers provided already exist in this class section", HTTPStatus.BAD_REQUEST,

        return True, "success", HTTPStatus.OK

    async def validate_admission_numbers(self, entity_id, admission_numbers):
        _columns = ["count(1) as count"]
        _where = {
            "entity_id = '%s'": entity_id,
            where_clause_for_multiple('admission_number', admission_numbers): "",
            "active = %s": True
        }
        _columns, _where = create_query_params(columns=_columns, where_dict=_where)
        query = f"SELECT {_columns} FROM {Tables.user_entity_details} WHERE {_where};"
        try:
            response = await self.db.fetch_all(query)
        except Exception as e:
            self.logger.error(f"failed to fetch user entity data due to {e}")
            return False, "Failed to fetch entity details", HTTPStatus.INTERNAL_SERVER_ERROR

        if response and response[0]["count"] > 0:
            return False, "Some of the admission numbers provided already exist in class", HTTPStatus.BAD_REQUEST,

        return True, "success", HTTPStatus.OK


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

    async def fetch_entity_users(
        self, entity_id: str, class_id: str = None, section_id: str = None,
        user_role: str = None, search: str = None
    ):
        _columns = [
            "ud.user_id", "ud.user_name", "ud.user_email", "ud.opti_code",
            "ued.user_role", "ued.permission_id", "ep.permission_name",
            "ued.class_id", "ued.section_id", "ued.roll_number", "ued.admission_number",
        ]
        _where = {
            "ued.entity_id = '%s'": entity_id,
            "ued.active = %s": True,
            "ud.active = %s": True,
        }
        if class_id:
            _where["ued.class_id = '%s'"] = class_id
        if section_id:
            _where["ued.section_id = '%s'"] = section_id
        if user_role:
            _where["ued.user_role = '%s'"] = user_role

        _columns, _where = create_query_params(columns=_columns, where_dict=_where)

        # Free-text search is bound as a query parameter (rather than embedded
        # via the %-substitution above) since it's arbitrary user input.
        values = {}
        search_clause = ""
        if search:
            search_clause = (
                " AND (ud.user_name LIKE :search OR ued.roll_number LIKE :search "
                "OR ued.admission_number LIKE :search)"
            )
            values["search"] = f"%{search}%"

        query = (
            f"SELECT {_columns} FROM {Tables.user_entity_details} ued "
            f"JOIN {Tables.user_details} ud ON ued.user_id = ud.user_id "
            f"LEFT JOIN {Tables.entity_permissions} ep ON ued.permission_id = ep.permission_id "
            f"WHERE {_where}{search_clause} ORDER BY ud.user_name;"
        )

        try:
            response = await self.db.fetch_all(query, values=values)
        except Exception as e:
            self.logger.error(f"failed to fetch entity users due to {e}")
            return False, "Failed to fetch entity users", HTTPStatus.INTERNAL_SERVER_ERROR, []

        data = [dict(row) for row in response]
        return True, "Successfully fetched entity users", HTTPStatus.OK, data
