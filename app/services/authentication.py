from _sha256 import sha256
from http import HTTPStatus

from app.enums import Tables


class Login:
    def __init__(self, db=None, logger=None):
        self.db = db
        self.logger = logger

    async def validate_authentication(self, user_email, user_password):
        _columns = ["ud.user_id", "ua.user_passkey", "ua.salt"]
        _where = f"ud.user_email = '{user_email}' and ud.active = true"

        query = f"""
        SELECT {', '.join(_columns)} from {Tables.user_details} ud JOIN {Tables.user_authentication} ua
        ON ud.user_id = ua.user_id WHERE {_where};"""

        try:
            response = await self.db.fetch_all(query)
        except Exception as e:
            self.logger.error(f"failed to fetch authentication details due to {e}")
            return False, "failed to fetch authentication details", HTTPStatus.INTERNAL_SERVER_ERROR

        if not response:
            return False, "user with the provided email doesn't exist", HTTPStatus.BAD_REQUEST

        response = response[0]

        status = self.verify_password(response["user_passkey"], response["salt"], user_password)
        if not status:
            return False, "incorrect password provided", HTTPStatus.BAD_REQUEST

        return True, "login successful", HTTPStatus.OK

    @staticmethod
    def verify_password(user_passkey: str, salt: str, provided_password: str) -> bool:
        provided_passkey = sha256(bytes("{}{}".format(provided_password, salt), encoding="utf-8")).hexdigest()
        if user_passkey != provided_passkey:
            return False
        return True
