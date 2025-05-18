
from fastapi import APIRouter, Request

from app.models.user_details import UserCreationModel, GlobalUserCreationModel
from app.services.user_details import UserCreation
from app.utils import standard_response_generator
from app.core import login_required

user_details = APIRouter()


@user_details.post("/")
@login_required
async def _create_entity_user(request: Request, data: UserCreationModel):
    user_creation_processor = UserCreation(db=request.app.db, logger=request.app.logger, x_user=request.app.user)
    success, message, status_code, data = await user_creation_processor.create_entity_user(data.model_dump())
    return standard_response_generator(success, message, status_code, data)


@user_details.post("/global")
@login_required
async def _create_global_user(request: Request, data: GlobalUserCreationModel):
    user_creation_processor = UserCreation(db=request.app.db, logger=request.app.logger, x_user=request.app.user)
    success, message, status_code, data = await user_creation_processor.create_global_user(data.model_dump())
    return standard_response_generator(success, message, status_code, data)



