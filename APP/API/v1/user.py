from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Response, status
from sqlalchemy import exists, func, literal, select
from sqlalchemy.orm import selectinload

from APP.core.db import SessionDependency
from APP.core.dependencies import CurrentUserDependency, OptionalUserDependency
from APP.models.follow import Follow
from APP.models.user import User
from APP.schemas.genre import GenreOut
from APP.schemas.preferences import FavoriteGenresPut
from APP.schemas.user import UserMe, UserOut
from APP.services.preferences import favorite_genres, replace_favorite_genres

router = APIRouter(tags=["users"])


@router.get("/me", response_model=UserMe)
async def me(
    user: CurrentUserDependency, response: Response, session: SessionDependency
) -> UserMe:
    response.headers["Cache-Control"] = "no-store"
    return await profile(session, user.id, user, UserMe)


@router.get(
    "/users/{user_id}", response_model=UserOut, openapi_extra={"security": [{}]}
)
async def public_profile(
    user_id: Annotated[int, Path(gt=0)],
    session: SessionDependency,
    viewer: OptionalUserDependency,
    response: Response,
) -> UserOut:
    response.headers["Cache-Control"] = "no-store"
    return await profile(session, user_id, viewer, UserOut)


async def profile(session, user_id, viewer, schema):
    followers = (
        select(func.count())
        .select_from(Follow)
        .where(Follow.target_type == "user", Follow.target_id == User.id)
        .correlate(User)
        .scalar_subquery()
    )
    following = (
        select(func.count())
        .select_from(Follow)
        .where(Follow.follower_id == User.id)
        .correlate(User)
        .scalar_subquery()
    )
    mine = (
        exists()
        .where(
            Follow.follower_id == viewer.id,
            Follow.target_type == "user",
            Follow.target_id == User.id,
        )
        .correlate(User)
        if viewer is not None
        else literal(False)
    )
    row = (
        await session.execute(
            select(
                User,
                followers.label("followers_count"),
                following.label("following_count"),
                mine.label("is_followed_by_me"),
            )
            .options(selectinload(User.city))
            .where(User.id == user_id, User.is_active.is_(True))
        )
    ).one_or_none()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    output = schema.model_validate(row.User)
    output.followers_count = row.followers_count
    output.following_count = row.following_count
    output.is_followed_by_me = row.is_followed_by_me
    return output


@router.get("/me/favorite-genres", response_model=list[GenreOut])
async def get_favorite_genres(
    session: SessionDependency, user: CurrentUserDependency, response: Response
):
    response.headers["Cache-Control"] = "no-store"
    return await favorite_genres(session, user)


@router.put("/me/favorite-genres", response_model=list[GenreOut])
async def put_favorite_genres(
    payload: FavoriteGenresPut,
    session: SessionDependency,
    user: CurrentUserDependency,
    response: Response,
):
    response.headers["Cache-Control"] = "no-store"
    return await replace_favorite_genres(session, user, payload)
