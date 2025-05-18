import uuid
from _sha256 import sha256
from http import HTTPStatus

from app.enums import Tables
from app.utils import get_passkey, create_update_query_with_values


class Login:
    def __init__(self, db=None, logger=None):
        self.db = db
        self.logger = logger

    async def validate_authentication(self, user_email, user_password, validate_only=False):
        _columns = ["ud.user_id", "ua.user_passkey", "ua.salt"]
        _where = f"ud.user_email = '{user_email}' and ud.active = true"

        query = f"""
        SELECT {', '.join(_columns)} from {Tables.user_details} ud JOIN {Tables.user_authentication} ua
        ON ud.user_id = ua.user_id WHERE {_where};"""

        try:
            response = await self.db.fetch_all(query)
        except Exception as e:
            self.logger.error(f"failed to fetch authentication details due to {e}")
            return False, "failed to fetch authentication details", HTTPStatus.INTERNAL_SERVER_ERROR, {}

        if not response:
            return False, "user with the provided email doesn't exist", HTTPStatus.BAD_REQUEST, {}

        response = response[0]

        status = self.verify_password(response["user_passkey"], response["salt"], user_password)
        if not status:
            return False, "incorrect password provided", HTTPStatus.BAD_REQUEST, {}

        if validate_only:
            return True, "validation successful", HTTPStatus.OK, {"authentication_details": response}

        return await self.update_authentication_token(response["user_id"])

    async def update_authentication_token(self, user_id: str):
        auth_token = str(uuid.uuid4())
        query = f"""UPDATE {Tables.user_details} SET authentication_token = '{auth_token}' WHERE user_id = '{user_id}';"""

        try:
            await self.db.execute(query)
        except Exception as e:
            self.logger.error(f"failed to execute update query due to {e}")
            return False, "failed to authenticate user", HTTPStatus.INTERNAL_SERVER_ERROR, {}

        return True, "login successful", HTTPStatus.OK, {"user_id": user_id, "authenticationtoken": auth_token}

    @staticmethod
    def verify_password(user_passkey: str, salt: str, provided_password: str) -> bool:
        provided_passkey = get_passkey(provided_password, salt)
        if user_passkey != provided_passkey:
            return False
        return True

    async def update_password(self, user_email, old_password, new_password):
        success, message, status_code, data = await self.validate_authentication(
            user_email=user_email,
            user_password=old_password,
            validate_only=True
        )
        if not success:
            return success, message, status_code, data

        authentication_details = data.get("authentication_details", {})
        new_passkey = get_passkey(new_password, authentication_details["salt"])

        query, values = create_update_query_with_values(
            Tables.user_authentication,
            update_data={"user_passkey": new_passkey},
            where_condition={"user_id": authentication_details["user_id"]}
        )
        try:
            await self.db.execute(query=query, values=values)
        except Exception as e:
            self.logger.error(f"failed to execute query due to {e}")
            return False, "Failed to update password", HTTPStatus.INTERNAL_SERVER_ERROR

        return True, "Successfully updated password", HTTPStatus.OK
