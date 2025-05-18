from typing import List, Optional

from pydantic import BaseModel, field_validator, model_validator, EmailStr


class ValidateLogin(BaseModel):
    user_email: EmailStr
    user_password: str


class UpdatePassword(BaseModel):
    old_password: str
    new_password: str
    user_email: EmailStr

    @model_validator(mode="after")
    def validate_passwords(cls, v):
        if v.old_password == v.new_password:
            raise ValueError("old and new passwords should be different")
        return v
