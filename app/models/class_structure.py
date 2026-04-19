from typing import List, Optional

from pydantic import BaseModel, Field


class SectionInput(BaseModel):
    section_name: str = Field(min_length=1, max_length=100)


class CreateClassModel(BaseModel):
    entity_id: str = Field(min_length=12, max_length=12)
    class_name: str = Field(min_length=1, max_length=100)
    sections: Optional[List[SectionInput]] = None


class BulkCreateClassModel(BaseModel):
    entity_id: str = Field(min_length=12, max_length=12)
    classes: List[CreateClassModel] = Field(min_length=1)


class RenameClassModel(BaseModel):
    entity_id: str = Field(min_length=12, max_length=12)
    class_id: str = Field(min_length=12, max_length=12)
    class_name: str = Field(min_length=1, max_length=100)


class AddSectionsModel(BaseModel):
    entity_id: str = Field(min_length=12, max_length=12)
    class_id: str = Field(min_length=12, max_length=12)
    sections: List[SectionInput] = Field(min_length=1)


class RenameSectionModel(BaseModel):
    entity_id: str = Field(min_length=12, max_length=12)
    class_id: str = Field(min_length=12, max_length=12)
    section_id: str = Field(min_length=12, max_length=12)
    section_name: str = Field(min_length=1, max_length=100)


class DeleteClassModel(BaseModel):
    entity_id: str = Field(min_length=12, max_length=12)
    class_ids: List[str] = Field(min_length=1)


class DeleteSectionModel(BaseModel):
    entity_id: str = Field(min_length=12, max_length=12)
    class_id: str = Field(min_length=12, max_length=12)
    section_ids: List[str] = Field(min_length=1)


class GetClassStructure(BaseModel):
    entity_id: str = Field(min_length=12, max_length=12)
