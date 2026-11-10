"""Пересчёт весов и агрегатов: python -m APP.recalculate_ratings."""

import asyncio
import logging
from collections import Counter

from sqlalchemy import func, or_, select, text, update

from APP.core.config import get_settings
from APP.core.db import create_engine, create_session_factory
from APP.core.logging import configure_logging
from APP.models.event_log import EventLog
from APP.models.rating import Rating
from APP.models.user import User
from APP.services.experience import user_rating_weight
from APP.services.ratings import TARGET_MODELS

logger = logging.getLogger(__name__)


async def recalculate_ratings(session, settings):
    result = {"users_updated": 0, "ratings_updated": 0, "targets_updated": 0}
    async with session.begin():
        # Блокируем записи, чтобы PUT/DELETE не меняли агрегаты во время пересчёта.
        await session.execute(
            text(
                "LOCK TABLE users, artists, albums, tracks, venues, ratings IN EXCLUSIVE MODE"
            )
        )
        users = {user.id: user for user in (await session.scalars(select(User))).all()}
        weights = {
            key: user_rating_weight(user, settings) for key, user in users.items()
        }
        previous = {key: user.weight for key, user in users.items()}
        changed = Counter()
        for rating in (await session.scalars(select(Rating))).all():
            if rating.weight != weights[rating.user_id]:
                rating.weight = weights[rating.user_id]
                changed[rating.user_id] += 1
                result["ratings_updated"] += 1
        for key, user in users.items():
            if user.weight != weights[key]:
                user.weight = weights[key]
                result["users_updated"] += 1
            if previous[key] != weights[key] or changed[key]:
                session.add(
                    EventLog(
                        actor_id=None,
                        action="rating_weights_recalculated",
                        target_type="user",
                        target_id=key,
                        is_public=False,
                        payload={
                            "previous_weight": float(previous[key]),
                            "weight": float(weights[key]),
                            "ratings_updated": changed[key],
                        },
                    )
                )
        await session.flush()
        for kind, model in TARGET_MODELS.items():
            totals = (
                select(
                    Rating.target_id,
                    func.sum(Rating.value * Rating.weight).label("rating_sum"),
                    func.sum(Rating.weight).label("rating_weight"),
                    func.count().label("ratings_count"),
                )
                .where(Rating.target_type == kind)
                .group_by(Rating.target_id)
                .subquery()
            )
            stats = (
                select(
                    model.id,
                    *[
                        func.coalesce(totals.c[key], 0).label(key)
                        for key in ("rating_sum", "rating_weight", "ratings_count")
                    ],
                )
                .outerjoin(totals, model.id == totals.c.target_id)
                .cte("rating_totals")
            )
            statement = (
                update(model)
                .where(
                    model.id == stats.c.id,
                    or_(
                        *[
                            getattr(model, key) != stats.c[key]
                            for key in ("rating_sum", "rating_weight", "ratings_count")
                        ]
                    ),
                )
                .values(
                    rating_sum=stats.c.rating_sum,
                    rating_weight=stats.c.rating_weight,
                    ratings_count=stats.c.ratings_count,
                    updated_at=model.updated_at,
                )
                .execution_options(synchronize_session=False)
            )
            result["targets_updated"] += (await session.execute(statement)).rowcount
    return result


async def run():
    settings = get_settings()
    configure_logging(settings.log_level)
    engine = create_engine(settings)
    try:
        async with create_session_factory(engine)() as session:
            result = await recalculate_ratings(session, settings)
        logger.info(
            "Rating weights recalculated", extra={"recalculation_result": result}
        )
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run())
