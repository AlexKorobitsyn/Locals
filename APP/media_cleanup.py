import argparse
import asyncio
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from starlette.concurrency import run_in_threadpool

from APP.core.config import get_settings
from APP.core.db import create_engine, create_session_factory
from APP.core.logging import configure_logging
from APP.core.storage import create_storage
from APP.models.media import Media
from APP.services.activity import record_event

logger = logging.getLogger(__name__)
DEFAULT_STALE_HOURS = 24


async def cleanup(stale_hours):
    settings = get_settings()
    configure_logging(settings.log_level)
    storage, engine = create_storage(settings), create_engine(settings)
    if storage is None:
        raise RuntimeError("S3 configuration is required")
    try:
        async with create_session_factory(engine)() as session:
            async with session.begin():
                rows = (
                    await session.scalars(
                        select(Media)
                        .where(
                            Media.status == "pending",
                            Media.created_at
                            < datetime.now(UTC) - timedelta(hours=stale_hours),
                        )
                        .with_for_update(skip_locked=True)
                    )
                ).all()
                for media in rows:
                    await run_in_threadpool(storage.delete, media.object_key)
                    record_event(
                        session,
                        media.user_id,
                        "media_pending_removed",
                        "media",
                        media.id,
                        public=False,
                    )
                    await session.delete(media)
                logger.info("Pending uploads cleaned", extra={"count": len(rows)})
    finally:
        storage.close()
        await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stale-hours", type=int, default=DEFAULT_STALE_HOURS)
    arguments = parser.parse_args()
    if arguments.stale_hours <= 0:
        parser.error("--stale-hours must be positive")
    asyncio.run(cleanup(arguments.stale_hours))
