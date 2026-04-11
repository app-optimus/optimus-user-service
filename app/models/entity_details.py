from typing import List, Optional

from pydantic import BaseModel, field_validator, model_validator, EmailStr, Field


class EntityCreationModel(BaseModel):
    name: str
    code: str
    address: str
    city: str
    state: str
    zip_code: str
    country: str
    head_name: str
    head_email: EmailStr
    selected_features: List
