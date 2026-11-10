import asyncio
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Event

import pytest
from sqlalchemy.exc import IntegrityError

import APP.services.catalog as catalog_service
import APP.services.ratings as rating_service
from APP.models.artist import Artist

pytestmark = pytest.mark.integration
TABLES = {"artist": "artists", "album": "albums", "track": "tracks", "venue": "venues"}


@pytest.fixture
def music(api_client, account):
    user, headers = account("owner")
    result = {"user": user, "headers": headers}
    for kind, body in [
        ("artist", {"name": "Solo"}),
        ("album", {"title": "Album"}),
        ("track", {"title": "Track", "duration": 120}),
    ]:
        if kind != "artist":
            body["artist_ids"] = [result["artist"]["id"]]
        response = api_client.post(
            "/api/v1/" + TABLES[kind], json=body, headers=headers
        )
        assert response.status_code == 201, response.text
        result[kind] = response.json()
    return result


def put(client, kind, target_id, value, headers):
    return client.put(
        "/api/v1/ratings",
        json={"target_type": kind, "target_id": target_id, "value": value},
        headers=headers,
    )


def remove(client, kind, target_id, headers):
    return client.delete(f"/api/v1/ratings/{kind}/{target_id}", headers=headers)


def assert_consistent(database, kind, target_id):
    row = database.execute(
        f"""SELECT t.rating_sum, t.rating_weight, t.ratings_count,
        (SELECT coalesce(sum(value * weight),0) FROM ratings WHERE target_type=:kind AND target_id=:id) AS actual_sum,
        (SELECT coalesce(sum(weight),0) FROM ratings WHERE target_type=:kind AND target_id=:id) AS actual_weight,
        (SELECT count(*) FROM ratings WHERE target_type=:kind AND target_id=:id) AS actual_count
        FROM {TABLES[kind]} t WHERE t.id=:id""",
        {"kind": kind, "id": target_id},
    )[0]
    assert row["rating_sum"] == row["actual_sum"]
    assert row["rating_weight"] == row["actual_weight"]
    assert row["ratings_count"] == row["actual_count"]
    return row


def test_weighted_create_replace_delete_and_my_rating(
    api_client, account, music, catalog_db
):
    listener, headers = account("listener")
    expert, expert_headers = account("expert")
    catalog_db.execute(
        "UPDATE users SET level='experienced', experience_points=100 WHERE id=:id",
        {"id": expert["id"]},
    )
    target = music["track"]["id"]
    first = put(api_client, "track", target, 4, headers)
    assert first.status_code == 200, first.text
    assert first.json()["rating_avg"] == 4
    assert first.json()["my_rating"] == 4 and first.json()["ratings_count"] == 1
    assert "rating_sum" not in first.json() and "rating_prior_mean" not in first.json()
    second = put(api_client, "track", target, 5, expert_headers)
    assert second.status_code == 200, second.text
    assert second.json()["rating_avg"] == pytest.approx((4 + 5 * 1.2) / 2.2)
    replacement = put(api_client, "track", target, 4.5, headers)
    assert replacement.status_code == 200 and replacement.json()["ratings_count"] == 2
    assert replacement.json()["rating_avg"] == pytest.approx((4.5 + 6) / 2.2)
    anonymous = api_client.get(f"/api/v1/tracks/{target}").json()
    assert (
        anonymous["my_rating"] is None
        and anonymous["rating_avg"] == replacement.json()["rating_avg"]
    )
    own = api_client.get(f"/api/v1/tracks/{target}", headers=headers).json()
    assert own["my_rating"] == 4.5
    assert (
        api_client.get("/api/v1/tracks", headers=expert_headers).json()["items"][0][
            "my_rating"
        ]
        == 5
    )
    assert (
        api_client.get("/api/v1/tracks", headers=music["headers"]).json()["items"][0][
            "my_rating"
        ]
        is None
    )
    assert_consistent(catalog_db, "track", target)
    deleted = remove(api_client, "track", target, headers)
    assert deleted.status_code == 200 and deleted.json()["my_rating"] is None
    assert deleted.json()["ratings_count"] == 1
    assert remove(api_client, "track", target, headers).json() == deleted.json()
    last = remove(api_client, "track", target, expert_headers)
    assert (
        last.status_code == 200
        and last.json()["ratings_count"] == 0
        and last.json()["rating_avg"] is None
    )
    row = assert_consistent(catalog_db, "track", target)
    assert row["rating_sum"] == row["rating_weight"] == 0


def test_weight_snapshot_on_level_change(api_client, music, catalog_db):
    user, headers = music["user"], music["headers"]
    target = music["artist"]["id"]
    assert put(api_client, "artist", target, 5, headers).status_code == 200
    catalog_db.execute(
        "UPDATE users SET level='experienced', experience_points=100 WHERE id=:id",
        {"id": user["id"]},
    )
    assert catalog_db.execute("SELECT weight FROM ratings")[0]["weight"] == 1
    assert (
        api_client.get(f"/api/v1/artists/{target}", headers=headers).json()[
            "rating_avg"
        ]
        == 5
    )
    assert put(api_client, "artist", target, 4.5, headers).status_code == 200
    assert catalog_db.execute("SELECT weight FROM ratings")[0]["weight"] == Decimal(
        "1.2"
    )
    assert catalog_db.execute(
        "SELECT weight FROM users WHERE id=:id", {"id": user["id"]}
    )[0]["weight"] == Decimal("1.2")
    catalog_db.execute(
        "UPDATE users SET level='green' WHERE id=:id", {"id": user["id"]}
    )
    assert remove(api_client, "artist", target, headers).status_code == 200
    assert assert_consistent(catalog_db, "artist", target)["actual_count"] == 0


@pytest.mark.parametrize(
    "level,points,weight",
    [
        ("green", 0, "1"),
        ("experienced", 100, "1.2"),
        ("experienced", 300, "1.4"),
        ("experienced", 700, "1.7"),
        ("experienced", 1500, "2"),
        ("experienced", 3000, "2.3"),
        ("experienced", 6000, "2.6"),
        ("experienced", 12000, "3"),
        ("experienced", 25000, "3.5"),
        ("moderator", 0, "4"),
        ("admin", 0, "4"),
    ],
)
def test_default_level_weights(api_client, music, catalog_db, level, points, weight):
    catalog_db.execute(
        "UPDATE users SET level=:level, experience_points=:points WHERE id=:id",
        {"level": level, "points": points, "id": music["user"]["id"]},
    )
    assert (
        put(api_client, "track", music["track"]["id"], 5, music["headers"]).status_code
        == 200
    )
    assert catalog_db.execute("SELECT weight FROM ratings")[0]["weight"] == Decimal(
        weight
    )
    progress = api_client.get("/api/v1/me/experience", headers=music["headers"]).json()
    assert progress["rating_weight"] == float(weight)
    assert len(progress["rating_level_weights"]) == 9


def test_every_target_type_and_colliding_ids(api_client, music, catalog_db):
    city = catalog_db.execute(
        "INSERT INTO cities (name,country,lat,lng,timezone) VALUES ('City','Country',50,60,'UTC') RETURNING id"
    )[0]["id"]
    venue = catalog_db.execute(
        "INSERT INTO venues (name,city_id,lat,lng) VALUES ('Venue',:city,50,60) RETURNING id",
        {"city": city},
    )[0]["id"]
    for kind, target in [
        (kind, music[kind]["id"]) for kind in ("artist", "album", "track")
    ] + [("venue", venue)]:
        response = put(api_client, kind, target, 3.5, music["headers"])
        assert response.status_code == 200, response.text
        assert (
            response.json()["target_type"] == kind
            and response.json()["my_rating"] == 3.5
        )
        assert_consistent(catalog_db, kind, target)
        if kind != "venue":
            detail = api_client.get(
                f"/api/v1/{TABLES[kind]}/{target}", headers=music["headers"]
            ).json()
            page = api_client.get(
                f"/api/v1/{TABLES[kind]}", headers=music["headers"]
            ).json()
            assert detail["my_rating"] == page["items"][0]["my_rating"] == 3.5
    assert catalog_db.execute("SELECT count(*) AS count FROM ratings")[0]["count"] == 4


@pytest.mark.parametrize("value", [0, 6, 4.1, 4.499, True, "4.5", None])
def test_rating_value_validation(api_client, music, value):
    assert (
        put(
            api_client, "track", music["track"]["id"], value, music["headers"]
        ).status_code
        == 422
    )


def test_auth_and_target_validation(api_client, music, catalog_db):
    headers = music["headers"]
    assert put(api_client, "track", music["track"]["id"], 4, {}).status_code == 401
    assert put(api_client, "user", 1, 4, headers).status_code == 422
    assert put(api_client, "track", 0, 4, headers).status_code == 422
    assert put(api_client, "track", 99999, 4, headers).status_code == 404
    assert remove(api_client, "track", 99999, headers).status_code == 404
    assert remove(api_client, "user", 1, headers).status_code == 422
    assert remove(api_client, "track", 0, headers).status_code == 422
    assert catalog_db.execute("SELECT count(*) AS count FROM ratings")[0]["count"] == 0


def test_rating_sort_nulls_and_settings(api_client, music, catalog_db):
    headers = music["headers"]
    ids = [music["artist"]["id"]]
    for name in ("Higher", "Unrated"):
        ids.append(
            api_client.post(
                "/api/v1/artists", headers=headers, json={"name": name}
            ).json()["id"]
        )
    api_client.app.state.settings.rating_prior_mean = Decimal("2.5")
    api_client.app.state.settings.rating_prior_strength = Decimal("10")
    for target, value in zip(ids[:2], (1, 5)):
        assert put(api_client, "artist", target, value, headers).status_code == 200
    page = api_client.get("/api/v1/artists?sort=-rating_avg", headers=headers).json()
    assert [item["id"] for item in page["items"]] == [ids[1], ids[0], ids[2]]
    assert page["items"][0]["rating_avg"] == 5
    assert [
        item["id"]
        for item in api_client.get("/api/v1/artists?sort=rating_avg").json()["items"]
    ] == [ids[0], ids[1], ids[2]]
    assert page["items"][2]["rating_avg"] is None
    assert (
        api_client.get("/api/v1/artists?offset=99", headers=headers).json()["items"]
        == []
    )


def test_fractional_weights_do_not_accumulate_rounding_error(
    api_client, music, catalog_db
):
    api_client.app.state.settings.rating_level_weights[0] = Decimal("0.123457")
    for value in (1, 4.5, 2.5, 5, 1.5, 3, 4):
        assert (
            put(
                api_client, "track", music["track"]["id"], value, music["headers"]
            ).status_code
            == 200
        )
        assert_consistent(catalog_db, "track", music["track"]["id"])
    assert (
        remove(api_client, "track", music["track"]["id"], music["headers"]).status_code
        == 200
    )
    row = assert_consistent(catalog_db, "track", music["track"]["id"])
    assert row["actual_sum"] == row["actual_weight"] == 0


def test_concurrent_puts_of_same_user(api_client, music, catalog_db):
    target, headers = music["track"]["id"], music["headers"]
    with ThreadPoolExecutor(max_workers=8) as pool:
        responses = list(
            pool.map(
                lambda value: put(api_client, "track", target, value, headers),
                [1, 1.5, 2, 2.5, 3, 3.5, 4, 5],
            )
        )
    assert all(response.status_code == 200 for response in responses)
    row = assert_consistent(catalog_db, "track", target)
    assert row["ratings_count"] == 1


def test_concurrent_different_users_and_mixed_updates(
    api_client, music, account, catalog_db
):
    target = music["album"]["id"]
    accounts = [account(f"listener{index}") for index in range(8)]
    with ThreadPoolExecutor(max_workers=8) as pool:
        responses = list(
            pool.map(
                lambda pair: put(api_client, "album", target, 4.5, pair[1]), accounts
            )
        )
    assert all(response.status_code == 200 for response in responses)
    row = assert_consistent(catalog_db, "album", target)
    assert row["ratings_count"] == 8 and row["rating_sum"] == 36
    operations = [
        (lambda headers=headers: remove(api_client, "album", target, headers))
        if index % 2
        else (lambda headers=headers: put(api_client, "album", target, 2.5, headers))
        for index, (_, headers) in enumerate(accounts)
    ]
    with ThreadPoolExecutor(max_workers=8) as pool:
        responses = list(pool.map(lambda operation: operation(), operations))
    assert all(response.status_code == 200 for response in responses)
    row = assert_consistent(catalog_db, "album", target)
    assert row["ratings_count"] == 4 and row["rating_sum"] == 10


def test_concurrent_put_and_delete_same_vote(api_client, music, catalog_db):
    target, headers = music["artist"]["id"], music["headers"]
    with ThreadPoolExecutor(max_workers=8) as pool:
        responses = list(
            pool.map(
                lambda index: (
                    put(api_client, "artist", target, 4.5, headers)
                    if index % 2
                    else remove(api_client, "artist", target, headers)
                ),
                range(8),
            )
        )
    assert all(response.status_code == 200 for response in responses)
    assert assert_consistent(catalog_db, "artist", target)["ratings_count"] in (0, 1)


def test_catalog_creation_and_rating_have_no_fk_deadlock(
    api_client, music, catalog_db, monkeypatch
):
    artist_locked, user_locked = Event(), Event()
    original_rows, original_user = (
        catalog_service.related_rows,
        rating_service.lock_user,
    )

    async def rows(session, model, ids, owner=None):
        result = await original_rows(session, model, ids, owner)
        if model is Artist:
            artist_locked.set()
            assert await asyncio.to_thread(user_locked.wait, 5)
        return result

    async def user(session, user_id):
        result = await original_user(session, user_id)
        user_locked.set()
        return result

    monkeypatch.setattr(catalog_service, "related_rows", rows)
    monkeypatch.setattr(rating_service, "lock_user", user)
    with ThreadPoolExecutor(max_workers=2) as pool:
        album = pool.submit(
            api_client.post,
            "/api/v1/albums",
            headers=music["headers"],
            json={"title": "Concurrent", "artist_ids": [music["artist"]["id"]]},
        )
        assert artist_locked.wait(5)
        rating = pool.submit(
            put, api_client, "artist", music["artist"]["id"], 5, music["headers"]
        )
        assert album.result(timeout=10).status_code == 201
        assert rating.result(timeout=10).status_code == 200
    assert_consistent(catalog_db, "artist", music["artist"]["id"])


def test_rating_audit_failure_rolls_back_vote_aggregates_and_weight(
    api_client, music, catalog_db
):
    catalog_db.execute(
        "UPDATE users SET level='experienced' WHERE id=:id", {"id": music["user"]["id"]}
    )
    catalog_db.execute(
        "ALTER TABLE event_logs ADD CONSTRAINT reject_rating CHECK (action <> 'rating_set')"
    )
    with pytest.raises(IntegrityError):
        put(api_client, "track", music["track"]["id"], 5, music["headers"])
    assert catalog_db.execute("SELECT count(*) AS count FROM ratings")[0]["count"] == 0
    assert catalog_db.execute("SELECT weight FROM users")[0]["weight"] == 1
    assert (
        assert_consistent(catalog_db, "track", music["track"]["id"])["ratings_count"]
        == 0
    )


def test_database_constraints_and_target_foreign_keys(api_client, music, catalog_db):
    params = {"user": music["user"]["id"], "track": music["track"]["id"]}
    for changes in [
        {"value": 4.49},
        {"value": 4.499999999},
        {"value": 0},
        {"value": 6},
        {"track": 99999},
    ]:
        with pytest.raises(IntegrityError):
            catalog_db.execute(
                "INSERT INTO ratings (user_id,target_type,target_id,track_id,value,weight) VALUES (:user,'track',:track,:track,:value,1)",
                params | {"value": 4} | changes,
            )
    with pytest.raises(IntegrityError):
        catalog_db.execute(
            "INSERT INTO ratings (user_id,target_type,target_id,value,weight) VALUES (:user,'track',:track,4,1)",
            params,
        )
    with pytest.raises(IntegrityError):
        catalog_db.execute(
            "INSERT INTO ratings (user_id,target_type,target_id,track_id,value,weight) VALUES (:user,'artist',:track,:track,4,1)",
            params,
        )
    with pytest.raises(IntegrityError):
        catalog_db.execute(
            "INSERT INTO ratings (user_id,target_type,target_id,track_id,value,weight) VALUES (:user,'track',:track + 1,:track,4,1)",
            params,
        )
    assert (
        put(api_client, "track", params["track"], 4, music["headers"]).status_code
        == 200
    )
    with pytest.raises(IntegrityError):
        catalog_db.execute(
            "INSERT INTO ratings (user_id,target_type,target_id,track_id,value,weight) VALUES (:user,'track',:track,:track,5,1)",
            params,
        )
    with pytest.raises(IntegrityError):
        catalog_db.execute("DELETE FROM users WHERE id=:user", params)
    # Удаление самой цели каскадно удаляет оценки, без ссылок на чужие ID.
    catalog_db.execute("DELETE FROM tracks WHERE id=:track", params)
    assert catalog_db.execute("SELECT count(*) AS count FROM ratings")[0]["count"] == 0
