import asyncio

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context
from APP.core.config import get_settings
from APP.core.logging import configure_logging
from APP.models import Base

settings = get_settings()
configure_logging(settings.log_level)
target_metadata = Base.metadata


def configure_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    engine = create_async_engine(
        settings.database_url.get_secret_value(),
        poolclass=pool.NullPool,
        hide_parameters=True,
        connect_args={"timeout": settings.db_connect_timeout_seconds},
    )
    try:
        async with engine.connect() as connection:
            await connection.run_sync(configure_migrations)
    finally:
        await engine.dispose()


if context.is_offline_mode():
    context.configure(
        url=settings.database_url.get_secret_value(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()
elif context.config.attributes.get("connection") is not None:
    configure_migrations(context.config.attributes["connection"])
else:
    asyncio.run(run_async_migrations())
