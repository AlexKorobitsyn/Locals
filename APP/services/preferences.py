from fastapi import HTTPException
from sqlalchemy import delete, insert, select

from APP.models.genre import Genre, user_favorite_genres
from APP.schemas.genre import GenreOut
from APP.services.activity import record_event
from APP.services.ratings import lock_user


async def favorite_genres(session, user):
    rows = (
        await session.scalars(
            select(Genre)
            .join(user_favorite_genres)
            .where(user_favorite_genres.c.user_id == user.id)
            .order_by(Genre.name, Genre.id)
        )
    ).all()
    return [GenreOut.model_validate(row) for row in rows]


async def replace_favorite_genres(session, user, payload):
    async with session.begin():
        await lock_user(session, user.id)
        ids = sorted(payload.genre_ids)
        rows = (
            await session.scalars(
                select(Genre)
                .where(Genre.id.in_(ids))
                .order_by(Genre.id)
                .with_for_update(read=True, key_share=True)
            )
        ).all()
        if len(rows) != len(ids):
            raise HTTPException(status_code=404, detail="Genre not found")
        current = set(
            (
                await session.scalars(
                    select(user_favorite_genres.c.genre_id).where(
                        user_favorite_genres.c.user_id == user.id
                    )
                )
            ).all()
        )
        if current != set(ids):
            await session.execute(
                delete(user_favorite_genres).where(
                    user_favorite_genres.c.user_id == user.id
                )
            )
            if ids:
                await session.execute(
                    insert(user_favorite_genres),
                    [{"user_id": user.id, "genre_id": genre_id} for genre_id in ids],
                )
            record_event(
                session,
                user.id,
                "favorite_genres_updated",
                "user",
                user.id,
                public=False,
                payload={"genre_ids": ids},
            )
        output = [
            GenreOut.model_validate(row)
            for row in sorted(rows, key=lambda row: (row.name, row.id))
        ]
    return output
