from typing import List, Optional

from pydantic import BaseModel, field_validator, model_validator, EmailStr


class ValidateLogin(BaseModel):
    user_email: EmailStr
    user_password: str
