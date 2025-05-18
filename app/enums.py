from enum import Enum


class Tables:
    user_authentication = "user_authentication"
    user_details = "user_details"
    entity_permissions = "entity_permissions"
    user_entity_details = "user_entity_details"


class UserTypes(str, Enum):
    chief_admin = "chief admin"
    entity_admin = "entity admin"   # principal
    user = "user"   # both teacher and students


class UserRoles(str, Enum):
    principal = "principal"
    teacher = "teacher"
    student = "student"
