from fastapi import APIRouter, Request

from app.models.entity_details import EntityCreationModel
from app.services.entity_details import EntityCreation
from app.utils import standard_response_generator
from app.core import login_required

entity_details = APIRouter()


@entity_details.post('/')
@login_required
async def _create_entity(request: Request, data: EntityCreationModel):
    entity_creation_processor = EntityCreation(db=request.app.db, logger=request.app.logger, x_user=request.app.user)
    success, message, status_code = await entity_creation_processor.create_entity(data.model_dump())
    return standard_response_generator(success, message, status_code)
