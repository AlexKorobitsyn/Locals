from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from APP.core.metrics import REVIEWS_SUBMITTED
from APP.core.dependencies import require_owner_or_privileged
from APP.models.rating import Rating
from APP.models.review import Review
from APP.models.user import User
from APP.schemas.pagination import Page
from APP.schemas.review import ReviewCreate, ReviewOut, ReviewUpdate
from APP.schemas.user import UserShort
from APP.services.activity import record_event
from APP.services.engagement import set_engagement, with_engagement
from APP.services.ratings import lock_target, lock_user


def review_query(viewer):
    return with_engagement(
        select(Review, Rating, User)
        .join(Rating, Review.rating_id == Rating.id)
        .join(User, Rating.user_id == User.id),
        Review,
        "review",
        viewer,
    )


def review_output(row, viewer) -> ReviewOut:
    review, rating, author = row.Review, row.Rating, row.User
    result = ReviewOut(
        id=review.id,
        title=review.title,
        text=review.text,
        rating=float(rating.value),
        author=UserShort.model_validate(author),
        target_type=rating.target_type.value,
        target_id=rating.target_id,
        created_at=review.created_at,
        updated_at=review.updated_at,
        is_owner=viewer is not None and viewer.id == author.id,
    )
    return set_engagement(result, row)


async def get_review(session: AsyncSession, review_id: int, viewer) -> ReviewOut:
    row = (
        await session.execute(
            review_query(viewer)
            .where(Review.id == review_id)
            .execution_options(populate_existing=True)
        )
    ).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Review not found")
    return review_output(row, viewer)


async def list_reviews(session, viewer, limit, offset, kind=None, target_id=None):
    filters = []
    if kind is not None:
        filters.append(Rating.target_type == kind)
    if target_id is not None:
        filters.append(Rating.target_id == target_id)
    rows = (
        await session.execute(
            review_query(viewer)
            .where(*filters)
            .order_by(Review.created_at.desc(), Review.id.desc())
            .limit(limit)
            .offset(offset)
        )
    ).all()
    total = await session.scalar(
        select(func.count()).select_from(Review).join(Rating).where(*filters)
    )
    return Page(
        items=[review_output(row, viewer) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


async def create_review(
    session: AsyncSession, payload: ReviewCreate, user: User
) -> ReviewOut:
    try:
        async with session.begin():
            current_user = await lock_user(session, user.id)
            await lock_target(session, payload.target_type, payload.target_id)
            rating = await session.scalar(
                select(Rating).where(
                    Rating.user_id == user.id,
                    Rating.target_type == payload.target_type,
                    Rating.target_id == payload.target_id,
                )
            )
            if rating is None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Set a rating before writing a review",
                )
            if (
                await session.scalar(select(Review.id).where(Review.rating_id == rating.id))
                is not None
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, detail="Review already exists"
                )
            review = Review(rating_id=rating.id, title=payload.title, text=payload.text)
            session.add(review)
            await session.flush()
            from APP.services.gamification import review_award

            await review_award(session, current_user, rating, review.text)
            record_event(session, user.id, "review_created", "review", review.id)
            output = await get_review(session, review.id, user)
    except HTTPException as exc:
        outcome = "rejected" if exc.status_code//100 == 4 else "error"
        REVIEWS_SUBMITTED.labels(outcome=outcome).inc()
        raise
    except Exception:
        REVIEWS_SUBMITTED.labels(outcome="error").inc()
        raise
    else:
        REVIEWS_SUBMITTED.labels(outcome="success").inc()
        return output


async def change_review(
    session: AsyncSession,
    review_id: int,
    user: User,
    payload: ReviewUpdate | None = None,
):
    async with session.begin():
        current_user = await lock_user(session, user.id)
        row = (
            await session.execute(
                select(Review, Rating).join(Rating).where(Review.id == review_id)
            )
        ).one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail="Review not found")
        require_owner_or_privileged(row.Rating.user_id, user)
        await lock_target(session, row.Rating.target_type, row.Rating.target_id)
        review = await session.scalar(
            select(Review)
            .where(Review.id == review_id)
            .execution_options(populate_existing=True)
            .with_for_update()
        )
        if review is None:
            raise HTTPException(status_code=404, detail="Review not found")
        if payload is None:
            record_event(session, user.id, "review_deleted", "review", review.id)
            await session.delete(review)
            output = None
        else:
            for key, value in payload.model_dump(exclude_unset=True).items():
                setattr(review, key, value)
            from APP.services.gamification import review_award

            if row.Rating.user_id == user.id:
                await review_award(session, current_user, row.Rating, review.text)
            await session.flush()
            record_event(session, user.id, "review_updated", "review", review.id)
            output = await get_review(session, review.id, user)
    return output
