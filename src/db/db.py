from typing import AsyncGenerator

from sqlalchemy import Column, DateTime, MetaData, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, declared_attr

from src.config import settings


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "pk": "pk_%(table_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "ix": "ix_%(table_name)s_%(column_0_name)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
        }
    )

    @declared_attr
    def created_at(cls):
        return Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        )

    @declared_attr
    def updated_at(cls):
        return Column(
            DateTime(timezone=True),
            onupdate=func.now(),
            server_default=func.now(),
            nullable=False,
        )

    repr_cols_num = 3
    repr_cols = tuple()

    def __repr__(self) -> str:
        column_names = list(self.__table__.columns.keys())
        cols = []

        for idx, col_name in enumerate(column_names):
            if col_name in self.repr_cols or idx < self.repr_cols_num:
                value = getattr(self, col_name)
                cols.append(f"{col_name}={repr(value)}")

        cols_str = ", ".join(cols)
        return f"<{self.__class__.__name__}({cols_str})>"


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
)

async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
