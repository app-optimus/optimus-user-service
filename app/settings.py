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
