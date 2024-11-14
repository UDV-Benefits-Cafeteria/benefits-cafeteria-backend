from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.config import get_settings

settings = get_settings()
# Create a SQLAlchemy engine for asynchronous operations.
if settings.DEBUG:
    engine = create_async_engine(
        settings.DATABASE_URL, echo=settings.DEBUG, poolclass=NullPool, future=True
    )
else:
    engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)

# Create an async session factory using the configured engine.
async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
