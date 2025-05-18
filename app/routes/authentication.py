from fastapi import APIRouter, Depends, Request

from app.models.authentication import ValidateLogin, UpdatePassword
from app.services.authentication import Login
from app.utils import standard_response_generator

authentication = APIRouter()


@authentication.get("/login")
async def validate_login(request: Request, query_args: ValidateLogin = Depends()):
    login_processor = Login(db=request.app.db, logger=request.app.logger)
    success, message, status_code, data = await login_processor.validate_authentication(
        query_args.user_email,
        query_args.user_password
    )
    return standard_response_generator(success, message, status_code, data)


@authentication.patch("/password")
async def _update_password(request: Request, data: UpdatePassword):
    login_processor = Login(db=request.app.db, logger=request.app.logger)
    success, message, status_code = await login_processor.update_password(
        data.user_email,
        data.old_password,
        data.new_password
    )
    return standard_response_generator(success, message, status_code)
