import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
from databases import Database
from starlette.middleware.cors import CORSMiddleware

from app.routes.authentication import authentication
from app.settings import MYSQL_CONFIG, BASE_ROUTE, LOG_LEVEL, APP_NAME


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_logger(app)
    app.logger.info("✅ logger initialized")
    await init_db(app)
    app.logger.info("✅ MySQL database initialized and connected")

    yield

    await app.db.disconnect()
    app.logger.info("🛑 MySQL database connection closed")


def get_application() -> FastAPI:
    app = FastAPI(lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(authentication, tags=["authentication"], prefix=BASE_ROUTE)

    return app


app = get_application()


async def init_db(app: FastAPI):
    db_config = MYSQL_CONFIG
    DATABASE_URL = (
        f"mysql+aiomysql://{db_config['USER']}:{db_config['PASSWORD']}"
        f"@{db_config['HOST']}:{db_config['PORT']}/{db_config['NAME']}"
    )
    app.db = Database(DATABASE_URL)
    await app.db.connect()


def init_logger(app: FastAPI):
    extra = {"app_name": APP_NAME}
    log_format = f"%(asctime)s %(levelname)s {APP_NAME} \
    %(threadName)s %(module)s %(funcName)s %(message)s"
    logging.basicConfig(level=LOG_LEVEL, format=log_format, force=True)
    logger = logging.getLogger(__name__)
    logger = logging.LoggerAdapter(logger, extra)
    app.logger = logger
