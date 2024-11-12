from contextlib import asynccontextmanager

import redis.asyncio as redis
import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi_limiter import FastAPILimiter
from starlette.middleware.cors import CORSMiddleware

from src.api.v1 import router as api_v1_router
from src.config import get_settings
from src.middlewares.server_error_middleware import CatchServerErrorMiddleware
from src.middlewares.session_middleware import SessionMiddleware
from src.services.sessions import SessionsService
from src.utils.elastic_index import SearchService

settings = get_settings()


async def initialize_redis_limiter(redis_url: str) -> None:
    """
    Initializes the Redis limiter for request rate limiting.

    Args:
        redis_url (str): The URL to connect to the Redis server used for rate limiting.
    """
    redis_connection_limiter = redis.from_url(
        redis_url, encoding="utf-8", decode_responses=True
    )
    await FastAPILimiter.init(redis_connection_limiter)


async def initialize_resources() -> None:
    """
    Initializes resources required by the application, such as search indices
    and Redis limiter.
    """
    await SearchService().create_benefits_index()
    await SearchService().create_users_index()
    await initialize_redis_limiter(settings.REDIS_LIMITER_URL)


def add_middlewares(application: FastAPI, sessions_service: SessionsService) -> None:
    """
    Adds necessary middleware components to the FastAPI application.

    Args:
        application (FastAPI): The FastAPI application instance.
        sessions_service (SessionsService): The service used to manage user sessions.
    """
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOW_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(
        SessionMiddleware,
        sessions_service=sessions_service,
        session_expire_time=settings.SESSION_EXPIRE_TIME,
        refresh_threshold=settings.SESSION_REFRESH_THRESHOLD,
    )
    if not settings.DEBUG:
        application.add_middleware(
            TrustedHostMiddleware, allowed_hosts=settings.ALLOW_HOSTS
        )
        application.add_middleware(CatchServerErrorMiddleware)


def configure_sentry() -> None:
    """
    Configures Sentry for error tracking and performance monitoring.
    """
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        profiles_sample_rate=settings.SENTRY_SAMPLE_PROFILER_RATE,
        environment=settings.SENTRY_ENVIRONMENT,
    )


def create_application() -> FastAPI:
    """
    Creates and configures the FastAPI application instance, setting up
    resources, middlewares, and routing.

    Returns:
        FastAPI: The configured FastAPI application instance.
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """
        Asynchronous context manager for initializing resources
        during the application's lifespan.

        Args:
            app (FastAPI): The FastAPI application instance.
        """
        await initialize_resources()
        yield

    application = FastAPI(
        debug=settings.DEBUG,
        title=settings.APP_TITLE,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )

    sessions_service = SessionsService()

    add_middlewares(application, sessions_service)

    if not settings.DEBUG:
        configure_sentry()

    application.include_router(api_v1_router, prefix=settings.API_PREFIX)

    return application
