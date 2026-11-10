import logging
from decimal import Decimal
from types import SimpleNamespace

from fastapi import HTTPException, status
from sqlalchemy import and_, case, literal, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from APP.core.config import Settings
from APP.core.constants import RatingTarget
from APP.core.dependencies import unauthorized
from APP.models.album import Album
from APP.models.artist import Artist
from APP.models.event_log import EventLog
from APP.models.rating import Rating
from APP.models.review import Review
from APP.models.track import Track
from APP.models.user import User
from APP.models.venue import Venue
from APP.schemas.rating import RatingPut, RatingResult
from APP.services.experience import user_rating_weight

TARGET_MODELS = {
    RatingTarget.track: Track,
    RatingTarget.album: Album,
    RatingTarget.artist: Artist,
    RatingTarget.venue: Venue,
}


def rating_average_expression(model):
    return case(
        ((model.ratings_count == 0) | (model.rating_weight == 0), None),
        else_=model.rating_sum / model.rating_weight,
    )


def rating_rank_expression(model, settings: Settings):
    return case(
        (model.ratings_count == 0, None),
        else_=(
            model.rating_sum
            + settings.rating_prior_strength * settings.rating_prior_mean
        )
        / (model.rating_weight + settings.rating_prior_strength),
    )


def with_my_rating(query, model, kind: str, viewer: User | None):
    if viewer is None:
        return query.add_columns(literal(None).label("my_rating"))
    return query.outerjoin(
        Rating,
        and_(
            Rating.target_type == kind,
            Rating.target_id == model.id,
            Rating.user_id == viewer.id,
        ),
    ).add_columns(Rating.value.label("my_rating"))


def set_rating_context(output, my_rating):
    output.my_rating = float(my_rating) if my_rating is not None else None
    return output


async def lock_user(session: AsyncSession, user_id: int) -> User:
    user = await session.scalar(
        select(User).where(User.id == user_id).with_for_update(of=User, key_share=True)
    )
    if user is None or not user.is_active:
        raise unauthorized()
    return user


async def lock_target(session: AsyncSession, kind: RatingTarget, target_id: int):
    target = await session.scalar(
        select(TARGET_MODELS[kind])
        .where(TARGET_MODELS[kind].id == target_id)
        .with_for_update()
    )
    if target is None or (
        kind == RatingTarget.venue and target.publication_status != "published"
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Rating target not found"
        )
    return target


def rating_result(target, kind: RatingTarget, my_rating) -> RatingResult:
    result = RatingResult(
        target_type=kind,
        target_id=target.id,
        rating_sum=target.rating_sum,
        rating_weight=target.rating_weight,
        ratings_count=target.ratings_count,
    )
    return set_rating_context(result, my_rating)


def record_rating_event(
    session: AsyncSession,
    user_id: int,
    kind: RatingTarget,
    target_id: int,
    action: str,
    value: Decimal | None = None,
) -> None:
    session.add(
        EventLog(
            actor_id=user_id,
            action=action,
            target_type=kind.value,
            target_id=target_id,
            payload={"value": float(value)} if value is not None else {},
            is_public=True,
        )
    )


async def put_rating(
    session: AsyncSession, payload: RatingPut, user: User, settings: Settings
) -> RatingResult:
    async with session.begin():
        current_user = await lock_user(session, user.id)
        # Все write-операции рейтинга сначала блокируют пользователя, затем цель.
        target = await lock_target(session, payload.target_type, payload.target_id)
        rating = await session.scalar(
            select(Rating).where(
                Rating.user_id == user.id,
                Rating.target_type == payload.target_type,
                Rating.target_id == payload.target_id,
            )
        )
        value = Decimal(str(payload.value))
        weight = user_rating_weight(current_user, settings)
        current_user.weight = weight
        old_sum, old_weight = Decimal("0"), Decimal("0")
        if rating is None:
            rating = Rating(
                user_id=user.id,
                target_type=payload.target_type,
                target_id=payload.target_id,
                **{f"{payload.target_type.value}_id": payload.target_id},
                value=value,
                weight=weight,
            )
            session.add(rating)
            target.ratings_count += 1
        else:
            old_sum, old_weight = rating.value * rating.weight, rating.weight
            rating.value, rating.weight = value, weight
        target.rating_sum += value * weight - old_sum
        target.rating_weight += weight - old_weight
        from APP.services.gamification import micro_award

        if target.user_id != current_user.id:
            await micro_award(
                session, current_user, "rating", payload.target_type, payload.target_id
            )
        await session.flush()
        record_rating_event(
            session,
            user.id,
            payload.target_type,
            payload.target_id,
            "rating_set",
            value,
        )
        result = rating_result(target, payload.target_type, value)
    if payload.target_type == RatingTarget.track and target.user_id is not None:
        from APP.services.experience import claim_quality

        try:
            await claim_quality(
                session, SimpleNamespace(id=target.user_id), settings, target.id
            )
        except (SQLAlchemyError, HTTPException):
            logging.getLogger(__name__).warning(
                "Experience reward deferred; retry through claim endpoint"
            )
    return result


async def delete_rating(
    session: AsyncSession,
    kind: RatingTarget,
    target_id: int,
    user: User,
    settings: Settings,
) -> RatingResult:
    async with session.begin():
        await lock_user(session, user.id)
        target = await lock_target(session, kind, target_id)
        rating = await session.scalar(
            select(Rating).where(
                Rating.user_id == user.id,
                Rating.target_type == kind,
                Rating.target_id == target_id,
            )
        )
        if rating is not None:
            review_id = await session.scalar(
                select(Review.id).where(Review.rating_id == rating.id)
            )
            if review_id is not None:
                record_rating_event(
                    session, user.id, kind, target_id, "review_removed_with_rating"
                )
            target.rating_sum -= rating.value * rating.weight
            target.rating_weight -= rating.weight
            target.ratings_count -= 1
            if target.ratings_count == 0:
                target.rating_sum = target.rating_weight = Decimal("0")
            await session.delete(rating)
            await session.flush()
            record_rating_event(session, user.id, kind, target_id, "rating_deleted")
        result = rating_result(target, kind, None)
    return result
