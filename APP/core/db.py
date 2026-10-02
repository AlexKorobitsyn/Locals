import asyncio
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from APP.core.config import Settings


def create_engine(settings: Settings) -> AsyncEngine:
    return create_async_engine(
        settings.database_url.get_secret_value(),
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout_seconds,
        pool_pre_ping=True,
        hide_parameters=True,
        connect_args={
            "timeout": settings.db_connect_timeout_seconds,
            "command_timeout": settings.db_command_timeout_seconds,
        },
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    # Границы транзакции и commit задаёт операция сервиса.
    async with request.app.state.session_factory() as session:
        session.info["settings"] = request.app.state.settings
        yield session


SessionDependency = Annotated[AsyncSession, Depends(get_session)]


async def check_database(engine: AsyncEngine, timeout_seconds: float) -> None:
    async with asyncio.timeout(timeout_seconds):
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
