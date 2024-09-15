from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.api.v1.router import router as api_v1_router
from src.config import get_app_settings


def get_application() -> FastAPI:
    settings = get_app_settings()

    settings.configure_logging()

    application = FastAPI(**settings.fastapi_kwargs)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_hosts,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(api_v1_router, prefix=settings.api_v1_prefix)

    return application


app = get_application()
