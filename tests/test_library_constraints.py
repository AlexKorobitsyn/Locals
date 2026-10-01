import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import async_sessionmaker
from test_library import music as music
from test_library import rate, result

from APP.core.constants import RatingTarget
from APP.models import User
from APP.schemas.review import ReviewCreate
from APP.services.library import set_favorite
from APP.services.ratings import delete_rating
from APP.services.reviews import create_review

pytestmark = pytest.mark.integration


def test_migration_backfills_liked_and_seeds_event_types(catalog_db):
    catalog_db.migrate("downgrade", "0003_ratings")
    user = catalog_db.execute(
        "INSERT INTO users(email,display_name,password_hash) VALUES ('old@example.com','Old user','hash') RETURNING id"
    )[0]["id"]
    catalog_db.migrate("upgrade", "head")
    rows = catalog_db.execute("SELECT user_id,kind,visibility FROM playlists")
    assert [(row["user_id"], row["kind"], row["visibility"]) for row in rows] == [
        (user, "liked", "private")
    ]
    assert len(catalog_db.execute("SELECT id FROM event_types")) == 3


def test_database_enforces_favorite_follow_playlist_consistency(
    catalog_db, api_client, music
):
    user, headers, artist, _, tracks = music
    track = tracks[0]["id"]
    liked = catalog_db.execute("SELECT id FROM playlists WHERE kind='liked'")[0]["id"]
    statements = [
        (
            "INSERT INTO favorites(user_id,entity_type,entity_id) VALUES (:user,'track',:track)",
            {},
        ),
        (
            "INSERT INTO favorites(user_id,entity_type,entity_id,artist_id) VALUES (:user,'track',:track,:artist)",
            {},
        ),
        (
            "INSERT INTO favorites(user_id,entity_type,entity_id,track_id,artist_id) VALUES (:user,'track',:track,:track,:artist)",
            {},
        ),
        (
            "INSERT INTO favorites(user_id,entity_type,entity_id,track_id) VALUES (:user,'track',99999,99999)",
            {},
        ),
        (
            "INSERT INTO follows(follower_id,target_type,target_id,user_id) VALUES (:user,'user',:user,:user)",
            {},
        ),
        (
            "INSERT INTO follows(follower_id,target_type,target_id) VALUES (:user,'artist',:artist)",
            {},
        ),
        ("INSERT INTO playlists(user_id,name,kind) VALUES (:user,'Liked','liked')", {}),
        ("UPDATE playlists SET visibility='public' WHERE id=:liked", {}),
        (
            "INSERT INTO playlist_tracks(playlist_id,track_id,position) VALUES (:liked,:track,-1)",
            {},
        ),
        (
            "INSERT INTO events(city_id,name,starts_at,stop_at,lat,lng) SELECT id,'Invalid',now(),now(),lat,lng FROM cities",
            {},
        ),
    ]
    catalog_db.execute(
        "INSERT INTO cities(name,country,lat,lng,timezone) VALUES ('City','Country',56,60,'UTC')"
    )
    params = dict(user=user["id"], track=track, artist=artist["id"], liked=liked)
    for statement, extra in statements:
        with pytest.raises(DBAPIError):
            catalog_db.execute(statement, {**params, **extra})


def test_concurrent_review_creation_is_unique(api_client, music, catalog_db):
    user, headers, _, _, tracks = music
    track = tracks[0]["id"]
    rate(api_client, headers, track)

    async def run():
        factory = async_sessionmaker(catalog_db.engine, expire_on_commit=False)

        async def create():
            async with factory() as session:
                return await create_review(
                    session,
                    ReviewCreate(target_type="track", target_id=track, text="text"),
                    User(id=user["id"]),
                )

        return await asyncio.wait_for(
            asyncio.gather(create(), create(), return_exceptions=True), timeout=10
        )

    responses = asyncio.run(run())
    assert (
        sum(
            isinstance(item, HTTPException) and item.status_code == 409
            for item in responses
        )
        == 1
    )
    assert catalog_db.execute("SELECT count(*) AS n FROM reviews")[0]["n"] == 1


def test_rating_delete_races_with_review_favorite_without_orphans(
    api_client, music, account, catalog_db
):
    user, headers, _, _, tracks = music
    other, _ = account("other")
    track = tracks[0]["id"]
    rate(api_client, headers, track)
    review = result(
        api_client.post(
            "/api/v1/reviews",
            headers=headers,
            json={"target_type": "track", "target_id": track, "text": "text"},
        ),
        201,
    )

    async def run():
        factory = async_sessionmaker(catalog_db.engine, expire_on_commit=False)

        async def delete():
            async with factory() as session:
                return await delete_rating(
                    session,
                    RatingTarget.track,
                    track,
                    User(id=user["id"]),
                    catalog_db.settings,
                )

        async def like():
            async with factory() as session:
                return await set_favorite(
                    session, "review", review["id"], User(id=other["id"])
                )

        return await asyncio.wait_for(
            asyncio.gather(delete(), like(), return_exceptions=True), timeout=10
        )

    responses = asyncio.run(run())
    assert all(
        not isinstance(item, Exception)
        or (isinstance(item, HTTPException) and item.status_code == 404)
        for item in responses
    )
    assert catalog_db.execute("SELECT count(*) AS n FROM reviews")[0]["n"] == 0
    assert catalog_db.execute("SELECT count(*) AS n FROM favorites")[0]["n"] == 0
