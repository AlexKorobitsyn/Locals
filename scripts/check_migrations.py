import asyncio
import logging
import os
from uuid import uuid4

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from alembic import command
from APP.core.config import Settings
from APP.core.logging import configure_logging

logger = logging.getLogger(__name__)


async def check():
    config = Config("alembic.ini")
    if len(ScriptDirectory.from_config(config).get_heads()) != 1:
        raise RuntimeError("Migrations must have exactly one head")
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        raise RuntimeError(
            "TEST_DATABASE_URL is required for isolated migration checks"
        )
    os.environ["DATABASE_URL"] = url
    settings = Settings()
    configure_logging(settings.log_level)
    schema = "migration_check_" + uuid4().hex
    bootstrap = create_async_engine(url, poolclass=NullPool, hide_parameters=True)
    engine = create_async_engine(
        url,
        poolclass=NullPool,
        hide_parameters=True,
        connect_args={"server_settings": {"search_path": schema}},
    )
    created = False
    try:
        async with bootstrap.begin() as connection:
            await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
            created = True
        async with engine.begin() as connection:

            def apply(sync_connection):
                config.attributes["connection"] = sync_connection
                command.upgrade(config, "head")
                command.check(config)
                command.downgrade(config, "base")
                command.upgrade(config, "head")
                command.check(config)

            await connection.run_sync(apply)
        logger.info("Isolated migration checks passed")
    finally:
        await engine.dispose()
        try:
            if created:
                async with bootstrap.begin() as connection:
                    await connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        finally:
            await bootstrap.dispose()


if __name__ == "__main__":
    asyncio.run(check())
