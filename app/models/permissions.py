from typing import List, Optional, Dict

from pydantic import BaseModel, field_validator, model_validator, EmailStr, Field


class GetEntityPermissions(BaseModel):
    entity_id: str


class PermissionModel(BaseModel):
    """
    Validate a single permission
    """

    read: Optional[bool]
    write: Optional[bool]

    class Config:
        extra = "ignore"

    @model_validator(mode="after")
    def one_of_read_or_write_must_be_present(cls, values: Dict) -> Dict:
        values = dict(values)
        assert (
                values["read"] is not None or values["write"] is not None
        ), "either one of read or write permission must be present"
        return {key: value for key, value in values.items() if key in ("read", "write") and value is not None}


class CreateEntityPermission(BaseModel):
    entity_id: str
    permission_name: str
    permissions: Dict[str, Dict[str, PermissionModel]]

    @field_validator("permissions")
    def permissions_cannot_be_empty(cls, val: Dict) -> Dict:
        assert len(val) > 0, "permission set cannot be empty"
        return val
