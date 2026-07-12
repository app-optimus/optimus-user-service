from fastapi import APIRouter, Depends, Request

from app.core import login_required, verify_permission
from app.models.subjects import (
    CreateSubjectModel,
    DeleteSubjectsModel,
    GetSubjects,
    RenameSubjectModel,
)
from app.services.subjects import SubjectService
from app.utils import standard_response_generator

subjects = APIRouter()


@subjects.get("/")
@login_required
@verify_permission(submodules=["subjects"])
async def _get_subjects(request: Request, query_args: GetSubjects = Depends()):
    processor = SubjectService(db=request.app.db, logger=request.app.logger, x_user=request.app.user)
    success, message, status_code, data = await processor.fetch_subjects(query_args.entity_id, query_args.class_id)
    return standard_response_generator(success, message, status_code, data)


@subjects.post("/", name="subjects")
@login_required
@verify_permission(submodules=["subjects"])
async def _create_subject(request: Request, data: CreateSubjectModel):
    processor = SubjectService(db=request.app.db, logger=request.app.logger, x_user=request.app.user)
    success, message, status_code = await processor.create_subject(
        data.entity_id, data.class_id, data.subject_name
    )
    return standard_response_generator(success, message, status_code)


@subjects.patch("/", name="rename_subject")
@login_required
@verify_permission(submodules=["subjects"])
async def _rename_subject(request: Request, data: RenameSubjectModel):
    processor = SubjectService(db=request.app.db, logger=request.app.logger, x_user=request.app.user)
    success, message, status_code = await processor.rename_subject(
        data.entity_id, data.class_id, data.subject_id, data.subject_name
    )
    return standard_response_generator(success, message, status_code)


@subjects.delete("/", name="delete_subjects")
@login_required
@verify_permission(submodules=["subjects"])
async def _delete_subjects(request: Request, data: DeleteSubjectsModel):
    processor = SubjectService(db=request.app.db, logger=request.app.logger, x_user=request.app.user)
    success, message, status_code = await processor.delete_subjects(
        data.entity_id, data.class_id, data.subject_ids
    )
    return standard_response_generator(success, message, status_code)
