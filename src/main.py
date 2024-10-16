from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.api.v1 import router as api_v1_router
from src.config import settings
from src.middlewares.csrf_middleware import CSRFMiddleware
from src.middlewares.session_middleware import SessionMiddleware
from src.services.sessions import SessionsService


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

    sessions_service = SessionsService()

    application.add_middleware(
        SessionMiddleware,
        sessions_service=sessions_service,
        session_expire_time=settings.SESSION_EXPIRE_TIME,
        refresh_threshold=settings.SESSION_REFRESH_THRESHOLD,
    )

    # Not adding CSRF middleware in dev mode
    if not settings.DEBUG:
        application.add_middleware(
            CSRFMiddleware,
            sessions_service=sessions_service,
            csrf_header_name="X-CSRF-Token",
        )

    application.include_router(api_v1_router, prefix=settings.API_PREFIX)

    return application


app = get_application()
