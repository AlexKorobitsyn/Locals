import asyncio
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker
from test_ratings import assert_consistent, put
from test_ratings import music as music

from APP.models.user import User
from APP.recalculate_ratings import recalculate_ratings
from APP.schemas.rating import RatingPut
from APP.services.ratings import put_rating

pytestmark = pytest.mark.integration


def recalculate(database):
    async def run():
        async with async_sessionmaker(
            database.engine, expire_on_commit=False
        )() as session:
            return await recalculate_ratings(session, database.settings)

    return asyncio.run(run())


def test_recalculates_all_targets_preserving_ratings_reviews_and_xp(
    api_client, account, music, catalog_db
):
    legend, headers = account("legend")
    _, other_headers = account("other")
    city = catalog_db.execute(
        "INSERT INTO cities(name,country,lat,lng,timezone) VALUES ('City','RU',56,60,'UTC') RETURNING id"
    )[0]["id"]
    venue = catalog_db.execute(
        "INSERT INTO venues(name,city_id,lat,lng) VALUES ('Venue',:city,56,60) RETURNING id",
        {"city": city},
    )[0]["id"]
    targets = [(kind, music[kind]["id"]) for kind in ("artist", "album", "track")]
    targets.append(("venue", venue))
    for kind, target in targets:
        assert put(api_client, kind, target, 5, headers).status_code == 200
        assert put(api_client, kind, target, 3, other_headers).status_code == 200
    review = api_client.post(
        "/api/v1/reviews",
        headers=headers,
        json={
            "target_type": "track",
            "target_id": music["track"]["id"],
            "text": "A review to preserve",
        },
    )
    assert review.status_code == 201
    catalog_db.execute(
        "UPDATE users SET experience_points=25000, level='experienced' WHERE id=:id",
        {"id": legend["id"]},
    )
    old_ratings = catalog_db.execute(
        "SELECT id, value, created_at FROM ratings ORDER BY id"
    )
    assert recalculate(catalog_db) == {
        "users_updated": 1,
        "ratings_updated": 4,
        "targets_updated": 4,
    }
    for kind, target in targets:
        row = assert_consistent(catalog_db, kind, target)
        assert row["ratings_count"] == 2
        assert row["rating_weight"] == Decimal("4.5")
        assert row["rating_sum"] == Decimal("20.5")
    assert (
        catalog_db.execute("SELECT id, value, created_at FROM ratings ORDER BY id")
        == old_ratings
    )
    assert (
        api_client.get(f"/api/v1/reviews/{review.json()['id']}").json()["rating"] == 5
    )
    assert (
        catalog_db.execute(
            "SELECT experience_points FROM users WHERE id=:id", {"id": legend["id"]}
        )[0]["experience_points"]
        == 25000
    )
    assert recalculate(catalog_db) == {
        "users_updated": 0,
        "ratings_updated": 0,
        "targets_updated": 0,
    }
    assert (
        catalog_db.execute(
            "SELECT count(*) AS total FROM event_logs WHERE action='rating_weights_recalculated'"
        )[0]["total"]
        == 1
    )


def test_recalculation_rolls_back_on_audit_failure(
    api_client, account, music, catalog_db
):
    legend, headers = account("legend")
    target = music["track"]["id"]
    assert put(api_client, "track", target, 5, headers).status_code == 200
    catalog_db.execute(
        "UPDATE users SET experience_points=25000 WHERE id=:id", {"id": legend["id"]}
    )
    catalog_db.execute(
        "ALTER TABLE event_logs ADD CONSTRAINT reject_recalculation CHECK (action <> 'rating_weights_recalculated')"
    )
    with pytest.raises(IntegrityError):
        recalculate(catalog_db)
    assert catalog_db.execute("SELECT weight FROM ratings")[0]["weight"] == 1
    assert (
        catalog_db.execute(
            "SELECT weight FROM users WHERE id=:id", {"id": legend["id"]}
        )[0]["weight"]
        == 1
    )
    assert assert_consistent(catalog_db, "track", target)["rating_weight"] == 1


def test_concurrent_rating_waits_for_recalculation(
    api_client, account, music, catalog_db, monkeypatch
):
    legend, headers = account("legend")
    target = music["track"]["id"]
    assert put(api_client, "track", target, 5, headers).status_code == 200
    catalog_db.execute(
        "UPDATE users SET experience_points=25000 WHERE id=:id", {"id": legend["id"]}
    )

    async def run():
        locked, release = asyncio.Event(), asyncio.Event()
        factory = async_sessionmaker(catalog_db.engine, expire_on_commit=False)
        async with factory() as maintenance, factory() as writer:
            original_execute = maintenance.execute

            async def execute(statement, *args, **kwargs):
                result = await original_execute(statement, *args, **kwargs)
                if str(statement).startswith("LOCK TABLE"):
                    locked.set()
                    await release.wait()
                return result

            monkeypatch.setattr(maintenance, "execute", execute)
            task = asyncio.create_task(
                recalculate_ratings(maintenance, catalog_db.settings)
            )
            await asyncio.wait_for(locked.wait(), timeout=5)
            write = asyncio.create_task(
                put_rating(
                    writer,
                    RatingPut(target_type="track", target_id=target, value=4),
                    User(id=legend["id"]),
                    catalog_db.settings,
                )
            )
            try:
                with pytest.raises(TimeoutError):
                    await asyncio.wait_for(asyncio.shield(write), timeout=0.1)
            finally:
                release.set()
            await asyncio.wait_for(asyncio.gather(task, write), timeout=10)

    asyncio.run(run())
    row = assert_consistent(catalog_db, "track", target)
    assert row["ratings_count"] == 1
    assert row["rating_weight"] == Decimal("3.5")
    assert row["rating_sum"] == 14
