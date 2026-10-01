from sqlalchemy import exists, func, literal, select

from APP.models.favorite import Favorite
from APP.models.follow import Follow


def with_engagement(query, model, kind, viewer):
    query = query.add_columns(
        select(func.count())
        .select_from(Favorite)
        .where(Favorite.entity_type == kind, Favorite.entity_id == model.id)
        .correlate(model)
        .scalar_subquery()
        .label("likes_count")
    )
    mine = (
        exists()
        .where(
            Favorite.user_id == viewer.id,
            Favorite.entity_type == kind,
            Favorite.entity_id == model.id,
        )
        .correlate(model)
        if viewer is not None
        else literal(False)
    )
    query = query.add_columns(mine.label("is_liked_by_me"))
    if kind in ("artist", "venue"):
        query = query.add_columns(
            select(func.count())
            .select_from(Follow)
            .where(Follow.target_type == kind, Follow.target_id == model.id)
            .correlate(model)
            .scalar_subquery()
            .label("followers_count")
        )
        following = (
            exists()
            .where(
                Follow.follower_id == viewer.id,
                Follow.target_type == kind,
                Follow.target_id == model.id,
            )
            .correlate(model)
            if viewer is not None
            else literal(False)
        )
        query = query.add_columns(following.label("is_followed_by_me"))
    return query


def set_engagement(output, row):
    for key in (
        "likes_count",
        "is_liked_by_me",
        "followers_count",
        "is_followed_by_me",
    ):
        if hasattr(output, key) and key in row._mapping:
            setattr(output, key, row._mapping[key])
    return output
