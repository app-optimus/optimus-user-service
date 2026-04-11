from typing import List, Optional

from pydantic import BaseModel, field_validator, model_validator, EmailStr, Field

from app.enums import UserRoles


class UserCreationModel(BaseModel):
    entity_id: str = Field(min_length=12, max_length=12)
    user_name: str
    user_email: EmailStr
    user_role: UserRoles
    permission_name: str
    opti_code: str = Field(default=None, min_length=1, max_length=10)


class GlobalUserCreationModel(BaseModel):
    user_name: str
    user_email: EmailStr


class UserUpdateModel(BaseModel):
    entity_id: str = Field(min_length=12, max_length=12)
    user_id: str
    user_name: Optional[str] = None
    user_email: Optional[EmailStr] = None
    user_role: Optional[UserRoles] = None
    permission_name: Optional[str] = None

    @model_validator(mode="after")
    def validate_at_least_one_field(self):
        updatable = [self.user_name, self.user_email, self.user_role, self.permission_name]
        if not any(v is not None for v in updatable):
            raise ValueError("At least one of user_name, user_email, user_role, or permission_name must be provided")
        return self


class BulkUserCreationModel(BaseModel):
    entity_id: str = Field(min_length=12, max_length=12)

