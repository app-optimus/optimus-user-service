from fastapi import APIRouter, Depends, Request

from app.core import login_required, verify_permission
from app.models.authentication import ValidateLogin
from app.models.permissions import GetEntityPermissions, CreateEntityPermission
from app.services.authentication import Login
from app.services.permissions import EntityPermissions
from app.utils import standard_response_generator

permissions = APIRouter()


@permissions.get("/entity")
async def get_entity_permissions(request: Request, query_args: GetEntityPermissions = Depends()):
    entity_permissions_processor = EntityPermissions(db=request.app.db, logger=request.app.logger)
    success, message, status_code, data = await entity_permissions_processor.fetch_entity_permissions(
        query_args.entity_id
    )
    return standard_response_generator(success, message, status_code, data)


@permissions.post("/entity", name="entity_permissions")
@login_required
@verify_permission(submodules=["permissions"])
async def _create_entity_permission(request: Request, data: CreateEntityPermission):
    entity_permissions_processor = EntityPermissions(db=request.app.db, logger=request.app.logger, x_user=request.app.user)
    success, message, status_code = await entity_permissions_processor.create_entity_permission(
        data.entity_id, data.permission_name, data.permissions
    )
    return standard_response_generator(success, message, status_code)

