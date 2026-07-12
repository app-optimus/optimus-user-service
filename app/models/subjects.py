from typing import List, Optional

from pydantic import BaseModel, Field


class CreateSubjectModel(BaseModel):
    entity_id: str = Field(min_length=12, max_length=12)
    class_id: str = Field(min_length=12, max_length=12)
    subject_name: str = Field(min_length=1, max_length=100)


class RenameSubjectModel(BaseModel):
    entity_id: str = Field(min_length=12, max_length=12)
    class_id: str = Field(min_length=12, max_length=12)
    subject_id: str = Field(min_length=12, max_length=12)
    subject_name: str = Field(min_length=1, max_length=100)


class DeleteSubjectsModel(BaseModel):
    entity_id: str = Field(min_length=12, max_length=12)
    class_id: str = Field(min_length=12, max_length=12)
    subject_ids: List[str] = Field(min_length=1)


class GetSubjects(BaseModel):
    entity_id: str = Field(min_length=12, max_length=12)
    class_id: Optional[str] = None
