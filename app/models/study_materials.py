from typing import Optional

from pydantic import BaseModel, Field

from app.enums import MaterialTypes


class GetStudyMaterials(BaseModel):
    entity_id: str = Field(min_length=12, max_length=12)
    class_id: Optional[str] = None
    section_id: Optional[str] = None
    subject_id: Optional[str] = None
    material_type: Optional[MaterialTypes] = None


class DeleteStudyMaterialModel(BaseModel):
    entity_id: str = Field(min_length=12, max_length=12)
    material_id: str = Field(min_length=12, max_length=12)
