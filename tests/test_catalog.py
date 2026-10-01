import asyncio

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import select
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import selectinload

from APP.models import (
    Album,
    Artist,
    ArtistMember,
    Base,
    City,
    Genre,
    Track,
    TrackArtist,
    User,
)
from APP.schemas.album import AlbumOut
from APP.schemas.track import TrackOut

pytestmark = pytest.mark.integration


def test_migration_matches_models_and_round_trips(catalog_db):
    tables = {
        row["tablename"]
        for row in catalog_db.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname=:schema",
            {"schema": catalog_db.schema},
        )
    }
    assert tables == set(Base.metadata.tables) | {"alembic_version"}

    async def compare():
        async with catalog_db.engine.connect() as connection:

            def differences(sync_connection):
                context = MigrationContext.configure(
                    sync_connection,
                    opts={
                        "compare_type": True,
                        "compare_server_default": True,
                    },
                )
                return compare_metadata(context, Base.metadata)

            return await connection.run_sync(differences)

    assert asyncio.run(compare()) == []
    catalog_db.migrate("downgrade", "base")
    remaining = catalog_db.execute(
        "SELECT tablename FROM pg_tables WHERE schemaname=:schema",
        {"schema": catalog_db.schema},
    )
    assert {row["tablename"] for row in remaining} == {"alembic_version"}
    catalog_db.migrate("upgrade", "head")
    assert asyncio.run(compare()) == []


def test_catalog_relationships_credits_and_orm_serialization(catalog_db):
    async def run():
        factory = async_sessionmaker(catalog_db.engine, expire_on_commit=False)
        async with factory() as session:
            async with session.begin():
                city = City(
                    name="Test city",
                    country="Test country",
                    lat=56,
                    lng=60,
                    timezone="UTC",
                )
                genre = Genre(name="Jazz", slug="jazz")
                user = User(
                    email="musician@example.com",
                    display_name="Musician",
                    password_hash="test-hash",
                    city=city,
                    favorite_genres=[genre],
                )
                artist = Artist(name="Solo", owner=user, genres=[genre])
                imported = Artist(name="Imported", user_id=None)
                artist.memberships.append(ArtistMember(user=user, role="vocals"))
                album = Album(
                    title="Release", artists=[artist, imported], genres=[genre]
                )
                track = Track(title="Track", duration=120, album=album, genres=[genre])
                track.artist_credits.extend(
                    [
                        TrackArtist(artist=artist, role="guitar"),
                        TrackArtist(artist=artist, role="vocals"),
                        TrackArtist(artist=imported, role="vocals"),
                    ]
                )
                session.add_all([user, artist, imported, album, track])
                await session.flush()
                track_id, album_id = track.id, album.id
            session.expunge_all()
            loaded = await session.scalar(
                select(Track)
                .where(Track.id == track_id)
                .options(
                    selectinload(Track.artists),
                    selectinload(Track.genres),
                    selectinload(Track.album).selectinload(Album.artists),
                    selectinload(Track.artist_credits).selectinload(TrackArtist.artist),
                )
            )
            assert len(loaded.artists) == 2
            assert {credit.role for credit in loaded.artist_credits} == {
                "guitar",
                "vocals",
            }
            assert (
                loaded.rating_sum == loaded.rating_weight == loaded.ratings_count == 0
            )
            output = TrackOut.model_validate(loaded).model_dump(mode="json")
            assert output["genres"][0]["slug"] == "jazz"
            assert len(output["artists"]) == 2
            album = await session.scalar(
                select(Album)
                .where(Album.id == album_id)
                .options(selectinload(Album.artists), selectinload(Album.genres))
            )
            assert AlbumOut.model_validate(album).genres[0].slug == "jazz"

    asyncio.run(run())


@pytest.mark.parametrize(
    "statement",
    [
        "INSERT INTO cities (name,country,lat,lng,timezone) VALUES ('City','Country',91,60,'UTC')",
        "INSERT INTO cities (name,country,lat,lng,timezone) VALUES ('City','Country',50,-181,'UTC')",
        "INSERT INTO genres (slug,name) VALUES ('Invalid Slug','Genre')",
        "INSERT INTO tracks (title,duration) VALUES ('Track',0)",
        "INSERT INTO tracks (title,duration) VALUES (' ',100)",
        "INSERT INTO artists (name,user_id) VALUES ('Artist',99999)",
        "INSERT INTO artists (name,rating_sum,rating_weight,ratings_count) VALUES ('Artist',6,1,1)",
        "INSERT INTO artists (name,rating_sum,rating_weight,ratings_count) VALUES ('Artist',4,1,0)",
        "INSERT INTO artists (name,rating_weight) VALUES ('Artist','NaN'::float8)",
        "INSERT INTO users (email,display_name,password_hash,weight) VALUES ('test@example.com','User','hash',0)",
        "INSERT INTO users (email,display_name,password_hash,weight) VALUES ('test@example.com','User','hash','Infinity'::float8)",
        "INSERT INTO users (email,display_name,password_hash,level) VALUES ('test@example.com','User','hash','artist')",
    ],
)
def test_database_rejects_invalid_catalog_values(catalog_db, statement):
    with pytest.raises(DBAPIError) as error:
        catalog_db.execute(statement)
    assert error.value.orig.sqlstate in {"23514", "23503", "22003"}


def test_nullable_city_region_is_still_unique(catalog_db):
    statement = "INSERT INTO cities (name,country,lat,lng,timezone) VALUES ('City','Country',50,60,'UTC')"
    catalog_db.execute(statement)
    with pytest.raises(IntegrityError):
        catalog_db.execute(statement)


def test_deleting_user_preserves_artist_and_cascades_membership(catalog_db):
    user_id = catalog_db.execute(
        "INSERT INTO users (email,display_name,password_hash) VALUES ('test@example.com','User','hash') RETURNING id"
    )[0]["id"]
    artist_id = catalog_db.execute(
        "INSERT INTO artists (name,user_id) VALUES ('Artist',:id) RETURNING id",
        {"id": user_id},
    )[0]["id"]
    catalog_db.execute(
        "INSERT INTO artist_members (artist_id,user_id) VALUES (:artist,:user)",
        {"artist": artist_id, "user": user_id},
    )
    catalog_db.execute("DELETE FROM users WHERE id=:id", {"id": user_id})
    assert (
        catalog_db.execute(
            "SELECT user_id FROM artists WHERE id=:id", {"id": artist_id}
        )[0]["user_id"]
        is None
    )
    assert (
        catalog_db.execute("SELECT count(*) AS count FROM artist_members")[0]["count"]
        == 0
    )


def test_credit_uniqueness_and_track_delete_cascade(catalog_db):
    artist_id = catalog_db.execute(
        "INSERT INTO artists (name) VALUES ('Artist') RETURNING id"
    )[0]["id"]
    track_id = catalog_db.execute(
        "INSERT INTO tracks (title,duration) VALUES ('Track',120) RETURNING id"
    )[0]["id"]
    params = {"artist": artist_id, "track": track_id}
    statement = "INSERT INTO track_artists (artist_id,track_id,role) VALUES (:artist,:track,'guitar')"
    catalog_db.execute(statement, params)
    with pytest.raises(IntegrityError):
        catalog_db.execute(statement, params)
    catalog_db.execute("DELETE FROM tracks WHERE id=:track", params)
    assert (
        catalog_db.execute("SELECT count(*) AS count FROM track_artists")[0]["count"]
        == 0
    )
