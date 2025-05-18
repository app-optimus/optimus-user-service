from typing import List, Optional

from pydantic import BaseModel, field_validator, model_validator, EmailStr, Field

from app.enums import UserRoles


class UserCreationModel(BaseModel):
    entity_id: str = Field(min_length=12, max_length=12)
    user_name: str
    user_email: EmailStr
    user_role: UserRoles
    permission_name: str
    user_code: str = Field(default=None, min_length=1, max_length=10)


class GlobalUserCreationModel(BaseModel):
    user_name: str
    user_email: EmailStr
