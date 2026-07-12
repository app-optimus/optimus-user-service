from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import FileResponse

from app.core import login_required
from app.models.study_materials import DeleteStudyMaterialModel, GetStudyMaterials
from app.services.study_materials import StudyMaterialService
from app.utils import standard_response_generator

study_materials = APIRouter()


@study_materials.get("/")
@login_required
async def _get_study_materials(request: Request, query_args: GetStudyMaterials = Depends()):
    processor = StudyMaterialService(db=request.app.db, logger=request.app.logger, x_user=request.app.user)
    success, message, status_code, data = await processor.fetch_materials(
        query_args.entity_id,
        query_args.class_id,
        query_args.section_id,
        query_args.subject_id,
        query_args.material_type.value if query_args.material_type else None,
    )
    return standard_response_generator(success, message, status_code, data)


@study_materials.post("/")
@login_required
async def _upload_study_material(
    request: Request,
    entity_id: str = Form(...),
    class_id: str = Form(...),
    section_id: str = Form(None),
    subject_id: str = Form(...),
    material_type: str = Form(...),
    title: str = Form(...),
    description: str = Form(None),
    file: UploadFile = File(...),
):
    processor = StudyMaterialService(db=request.app.db, logger=request.app.logger, x_user=request.app.user)
    success, message, status_code, data = await processor.upload_material(
        entity_id, class_id, section_id or None, subject_id, material_type, title, description, file
    )
    return standard_response_generator(success, message, status_code, data)


@study_materials.get("/{material_id}/download")
@login_required
async def _download_study_material(request: Request, material_id: str, entity_id: str):
    processor = StudyMaterialService(db=request.app.db, logger=request.app.logger, x_user=request.app.user)
    success, message, status_code, data = await processor.get_material_for_download(entity_id, material_id)
    if not success:
        return standard_response_generator(success, message, status_code, data)
    return FileResponse(
        path=data["absolute_path"], filename=data["file_name"], media_type=data["mime_type"]
    )


@study_materials.delete("/")
@login_required
async def _delete_study_material(request: Request, data: DeleteStudyMaterialModel):
    processor = StudyMaterialService(db=request.app.db, logger=request.app.logger, x_user=request.app.user)
    success, message, status_code = await processor.delete_material(data.entity_id, data.material_id)
    return standard_response_generator(success, message, status_code)
