from os import getenv
from dotenv import load_dotenv

load_dotenv(override=True)

APP_NAME = getenv("APP_NAME")
MYSQL_CONFIG = {
    "NAME": getenv("USERS_DB_NAME"),
    "HOST": getenv("DB_HOST"),
    "PORT": int(getenv("DB_PORT")),
    "USER": getenv("USERS_DB_USER"),
    "PASSWORD": getenv("USERS_DB_PASSWORD")
}

BASE_ROUTE = getenv("BASE_ROUTE")
LOG_LEVEL = getenv("LOG_LEVEL", "INFO")
MODULE_NAME = getenv("MODULE_NAME", "USER")
CUSTOM_HEADER_RPC_SECRET_KEY = getenv("RPC_SECRET_KEY")

# Temporary global authentication token, used until every client is wired up
# to a real login flow. When a request's `authenticationtoken` header matches
# this value, it is treated as a pre-authenticated chief-admin user.
GLOBAL_AUTH_TOKEN = getenv("GLOBAL_AUTH_TOKEN", "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")
GLOBAL_AUTH_USER_ID = getenv("GLOBAL_AUTH_USER_ID", "global-dev-user")

# Local-disk root for uploaded study material files. Kept behind the
# StorageService interface (app/services/storage.py) so this can later be
# swapped for a cloud bucket without touching callers.
STUDY_MATERIALS_STORAGE_DIR = getenv("STUDY_MATERIALS_STORAGE_DIR", "./uploads/study_materials")
