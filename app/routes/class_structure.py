from fastapi import APIRouter, Depends, Request

from app.core import login_required, verify_permission
from app.models.class_structure import (
    GetClassStructure,
    CreateClassModel,
    BulkCreateClassModel,
    RenameClassModel,
    DeleteClassModel,
    AddSectionsModel,
    RenameSectionModel,
    DeleteSectionModel,
)
from app.services.class_structure import ClassStructureService
from app.utils import standard_response_generator

class_structure = APIRouter()


@class_structure.get("/")
@login_required
@verify_permission(submodules=["class_structure"])
async def get_class_structure(request: Request, query_args: GetClassStructure = Depends()):
    processor = ClassStructureService(db=request.app.db, logger=request.app.logger, x_user=request.app.user)
    success, message, status_code, data = await processor.fetch_class_structure(query_args.entity_id)
    return standard_response_generator(success, message, status_code, data)


@class_structure.post("/", name="class_structure")
@login_required
@verify_permission(submodules=["class_structure"])
async def _create_class(request: Request, data: CreateClassModel):
    processor = ClassStructureService(db=request.app.db, logger=request.app.logger, x_user=request.app.user)
    success, message, status_code = await processor.create_class(data.model_dump())
    return standard_response_generator(success, message, status_code)


@class_structure.post("/bulk", name="bulk_class_structure")
@login_required
@verify_permission(submodules=["class_structure"])
async def _bulk_create_classes(request: Request, data: BulkCreateClassModel):
    processor = ClassStructureService(db=request.app.db, logger=request.app.logger, x_user=request.app.user)
    classes = [cls.model_dump() for cls in data.classes]
    success, message, status_code = await processor.bulk_create_classes(data.entity_id, classes)
    return standard_response_generator(success, message, status_code)


@class_structure.patch("/", name="rename_class")
@login_required
@verify_permission(submodules=["class_structure"])
async def _rename_class(request: Request, data: RenameClassModel):
    processor = ClassStructureService(db=request.app.db, logger=request.app.logger, x_user=request.app.user)
    success, message, status_code = await processor.rename_class(data.entity_id, data.class_id, data.class_name)
    return standard_response_generator(success, message, status_code)


@class_structure.delete("/", name="delete_class")
@login_required
@verify_permission(submodules=["class_structure"])
async def _delete_classes(request: Request, data: DeleteClassModel):
    processor = ClassStructureService(db=request.app.db, logger=request.app.logger, x_user=request.app.user)
    success, message, status_code = await processor.delete_classes(data.entity_id, data.class_ids)
    return standard_response_generator(success, message, status_code)


@class_structure.post("/section", name="add_sections")
@login_required
@verify_permission(submodules=["class_structure"])
async def _add_sections(request: Request, data: AddSectionsModel):
    processor = ClassStructureService(db=request.app.db, logger=request.app.logger, x_user=request.app.user)
    sections = [s.model_dump() for s in data.sections]
    success, message, status_code = await processor.add_sections(data.entity_id, data.class_id, sections)
    return standard_response_generator(success, message, status_code)


@class_structure.patch("/section", name="rename_section")
@login_required
@verify_permission(submodules=["class_structure"])
async def _rename_section(request: Request, data: RenameSectionModel):
    processor = ClassStructureService(db=request.app.db, logger=request.app.logger, x_user=request.app.user)
    success, message, status_code = await processor.rename_section(
        data.entity_id, data.class_id, data.section_id, data.section_name
    )
    return standard_response_generator(success, message, status_code)


@class_structure.delete("/section", name="delete_sections")
@login_required
@verify_permission(submodules=["class_structure"])
async def _delete_sections(request: Request, data: DeleteSectionModel):
    processor = ClassStructureService(db=request.app.db, logger=request.app.logger, x_user=request.app.user)
    success, message, status_code = await processor.delete_sections(data.entity_id, data.class_id, data.section_ids)
    return standard_response_generator(success, message, status_code)
