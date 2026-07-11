
from fastapi import APIRouter, Depends, Request, Form, File, UploadFile

from app.models.user_details import (
    UserCreationModel, GlobalUserCreationModel, BulkUserCreationModel, UserUpdateModel, GetEntityUsers
)
from app.services.user_details import UserCreation, UserDetails
from app.utils import standard_response_generator
from app.core import login_required

user_details = APIRouter()


@user_details.get("/entity-users")
@login_required
async def _get_entity_users(request: Request, query_args: GetEntityUsers = Depends()):
    user_details_processor = UserDetails(db=request.app.db, logger=request.app.logger)
    success, message, status_code, data = await user_details_processor.fetch_entity_users(
        query_args.entity_id,
        query_args.class_id,
        query_args.section_id,
        query_args.user_role.value if query_args.user_role else None,
        query_args.search,
    )
    return standard_response_generator(success, message, status_code, data)


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


@user_details.post("/bulk")
@login_required
async def _create_bulk_entity_user(
    request: Request,
    entity_id: str = Form(...),
    class_id: str = Form(...),
    section_id: str = Form(...),
    file: UploadFile = File(...),
):
    file_content = await file.read()
    user_creation_processor = UserCreation(db=request.app.db, logger=request.app.logger, x_user=request.app.user)
    success, message, status_code = await user_creation_processor.process_bulk_user_creation(
        entity_id, class_id, section_id, file_content
    )
    return standard_response_generator(success, message, status_code)


@user_details.patch("/")
@login_required
async def _update_user_details(request: Request, data: UserUpdateModel):
    user_creation_processor = UserCreation(db=request.app.db, logger=request.app.logger, x_user=request.app.user)
    success, message, status_code, data = await user_creation_processor.update_user_details(
        data.model_dump(exclude_none=True)
    )
    return standard_response_generator(success, message, status_code, data)


