import uvicorn

from src.application import create_application

app = create_application()

# from src.middlewares.csrf_middleware import CSRFMiddleware
from src.middlewares.server_error_middleware import CatchServerErrorMiddleware
from src.middlewares.session_middleware import SessionMiddleware
from src.services.sessions import SessionsService
from src.utils.elastic_index import SearchService


def get_application() -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await SearchService().create_benefits_index()
        await SearchService().create_users_index()

        redis_connection_limiter = redis.from_url(
            settings.REDIS_LIMITER_URL, encoding="utf-8", decode_responses=True
        )
        await FastAPILimiter.init(redis_connection_limiter)

        yield

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
        lifespan=lifespan,
    )

    sessions_service = SessionsService()

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

    # Not adding middleware in dev mode and on tests
    if not settings.DEBUG:
        # application.add_middleware(
        #     CSRFMiddleware,
        #     sessions_service=sessions_service,
        #     csrf_header_name="X-CSRF-Token",
        # )

        application.add_middleware(
            TrustedHostMiddleware, allowed_hosts=settings.ALLOW_HOSTS
        )

        application.add_middleware(
            CatchServerErrorMiddleware,
        )

    application.include_router(api_v1_router, prefix=settings.API_PREFIX)

    return application


app = get_application()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
    