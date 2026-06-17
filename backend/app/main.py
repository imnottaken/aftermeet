import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.meetings import router as meetings_router
from app.api.v1.health import router as health_router
from app.core.config import settings
from app.db.init_db import init_db

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)

    app.include_router(health_router)
    app.include_router(meetings_router)
    return app


app = create_app()
