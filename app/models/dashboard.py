from pydantic import BaseModel, Field


class GetStudentSectionCounts(BaseModel):
    entity_id: str = Field(min_length=12, max_length=12)


class GetHeadcountSummary(BaseModel):
    entity_id: str = Field(min_length=12, max_length=12)


class GetQuizSummary(BaseModel):
    entity_id: str = Field(min_length=12, max_length=12)
