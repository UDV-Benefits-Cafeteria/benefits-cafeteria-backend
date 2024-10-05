import logging

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.api.v1 import router as api_v1_router

from .config import settings

logging.basicConfig(level=logging.INFO)


def get_application() -> FastAPI:
    application = FastAPI(
        debug=settings.DEBUG,
        title=settings.APP_TITLE,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOW_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(api_v1_router, prefix=settings.API_PREFIX)

    return application


app = get_application()
