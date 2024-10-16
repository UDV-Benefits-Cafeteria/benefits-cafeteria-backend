import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.cors import CORSMiddleware

from src.api.v1 import router as api_v1_router
from src.config import settings
from src.middlewares.csrf_middleware import CSRFMiddleware
from src.middlewares.server_error_middleware import CatchServerErrorMiddleware
from src.middlewares.session_middleware import SessionMiddleware
from src.services.sessions import SessionsService


def get_application() -> FastAPI:
    # Not adding CSRF middleware in dev mode and on tests
    if not settings.DEBUG:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            profiles_sample_rate=settings.SENTRY_SAMPLE_PROFILER_RATE,
            environment=settings.SENTRY_ENVIRONMENT,
        )

    application = FastAPI(
        debug=settings.DEBUG,
        title=settings.APP_TITLE,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
    )

    sessions_service = SessionsService()

    application.add_middleware(
        SessionMiddleware,
        sessions_service=sessions_service,
        session_expire_time=settings.SESSION_EXPIRE_TIME,
        refresh_threshold=settings.SESSION_REFRESH_THRESHOLD,
    )

    # Not adding CSRF middleware in dev mode and on tests
    if not settings.DEBUG:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=settings.ALLOW_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        application.add_middleware(
            CSRFMiddleware,
            sessions_service=sessions_service,
            csrf_header_name="X-CSRF-Token",
        )

        application.add_middleware(
            HTTPSRedirectMiddleware,
        )

        application.add_middleware(
            TrustedHostMiddleware, allowed_hosts=settings.ALLOW_HOSTS
        )

        application.add_middleware(
            CatchServerErrorMiddleware,
        )

    application.include_router(api_v1_router, prefix=settings.API_PREFIX)

    return application


app = get_application()
