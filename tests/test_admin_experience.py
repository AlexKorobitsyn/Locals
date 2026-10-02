import asyncio
from concurrent.futures import ThreadPoolExecutor
from math import ceil
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker
from test_library import music as music
from test_library import result

from APP.create_admin import provision_admin
from APP.schemas.auth import RegisterInput
from APP.services.experience import claim_quality

pytestmark = pytest.mark.integration


def set_role(database, user, level, points=0):
    database.execute(
        "UPDATE users SET level=:level, experience_points=:points WHERE id=:id",
        {"id": user["id"], "level": level, "points": points},
    )


def login(client, name):
    tokens = result(
        client.post(
            "/api/v1/auth/login",
            json={"email": name + "@example.com", "password": "test-password-long"},
        )
    )
    return {"Authorization": "Bearer " + tokens["access_token"]}


def playable(database, owner, track, duration=120):
    media = database.execute(
        "INSERT INTO media(user_id,kind,status,object_key,filename,content_type,size,sha256,duration) VALUES (:owner,'audio','ready',:key,'music.wav','audio/wav',100,:sha,:duration) RETURNING id",
        {
            "owner": owner["id"],
            "key": uuid4().hex,
            "sha": "a" * 64,
            "duration": duration,
        },
    )[0]["id"]
    database.execute(
        "UPDATE tracks SET audio_media_id=:media WHERE id=:id",
        {"media": media, "id": track["id"]},
    )
    return media


def city(database):
    return database.execute(
        "INSERT INTO cities(name,country,lat,lng,timezone) VALUES ('City','RU',56,60,'Asia/Yekaterinburg') RETURNING id"
    )[0]["id"]


def credit_listen(client, database, headers, track_id):
    listening = result(
        client.post(f"/api/v1/tracks/{track_id}/listening", headers=headers), 201
    )
    for _ in range(ceil(listening["required_seconds"] / 20)):
        database.execute(
            "UPDATE listening_sessions SET last_seen_at=CURRENT_TIMESTAMP-interval '20 seconds' WHERE id=:id",
            {"id": listening["id"]},
        )
        listening = result(
            client.put(
                f"/api/v1/listening/{listening['id']}",
                headers=headers,
                json={"is_playing": True},
            )
        )
    return listening


@pytest.mark.parametrize(
    "level,points,scene,reference",
    [
        ("green", 0, False, False),
        ("experienced", 100, False, False),
        ("experienced", 300, False, False),
        ("experienced", 700, True, False),
        ("moderator", 0, True, True),
        ("admin", 0, True, True),
    ],
)
def test_role_matrix_for_scene_and_references(
    api_client, account, catalog_db, level, points, scene, reference
):
    user, headers = account()
    set_role(catalog_db, user, level, points)
    city_id = city(catalog_db)
    venue = api_client.post(
        "/api/v1/venues",
        headers=headers,
        json={"name": "Club", "city_id": city_id, "lat": 56, "lng": 60},
    )
    event = api_client.post(
        "/api/v1/events",
        headers=headers,
        json={
            "name": "Concert",
            "city_id": city_id,
            "starts_at": "2026-11-01T18:00:00Z",
        },
    )
    genre = api_client.post(
        "/api/v1/genres", headers=headers, json={"name": "Rock", "slug": "rock"}
    )
    assert venue.status_code == 201, venue.text
    assert event.status_code == 201, event.text
    assert genre.status_code == (201 if reference else 403), genre.text
    assert api_client.get("/api/v1/admin/users", headers=headers).status_code == (
        200 if level == "admin" else 403
    )


def test_venue_delete_preserves_linked_events(api_client, account, catalog_db):
    admin, headers = account("admin")
    set_role(catalog_db, admin, "admin")
    city_id = city(catalog_db)
    venue = result(
        api_client.post(
            "/api/v1/venues",
            headers=headers,
            json={"name": "Club", "city_id": city_id, "lat": 56, "lng": 60},
        ),
        201,
    )
    event = result(
        api_client.post(
            "/api/v1/events",
            headers=headers,
            json={
                "name": "Concert",
                "city_id": city_id,
                "venue_id": venue["id"],
                "starts_at": "2026-11-01T18:00:00Z",
            },
        ),
        201,
    )
    path = f"/api/v1/admin/venues/{venue['id']}"
    assert api_client.delete(path, headers=headers).status_code == 409
    assert api_client.get(f"/api/v1/venues/{venue['id']}").status_code == 200
    result(api_client.delete(f"/api/v1/events/{event['id']}", headers=headers), 204)
    result(api_client.delete(path, headers=headers), 204)
    assert api_client.get(f"/api/v1/venues/{venue['id']}").status_code == 404
    assert (
        len(
            catalog_db.execute("SELECT id FROM event_logs WHERE action='venue_deleted'")
        )
        == 1
    )


def test_admin_role_tier_status_and_session_revocation(api_client, account, catalog_db):
    admin, headers = account("admin")
    target, target_headers = account("target")
    set_role(catalog_db, admin, "admin")
    path = f"/api/v1/admin/users/{target['id']}"
    assert (
        api_client.put(
            path + "/level", headers=headers, json={"level": "admin"}
        ).status_code
        == 422
    )
    assert (
        result(api_client.put(path + "/experience", headers=headers, json={"tier": 3}))[
            "experience_points"
        ]
        == 700
    )
    assert api_client.get("/api/v1/me", headers=target_headers).status_code == 401
    target_headers = login(api_client, "target")
    assert (
        result(api_client.get("/api/v1/me/experience", headers=target_headers))[
            "experience_tier"
        ]
        == 3
    )
    result(api_client.put(path + "/status", headers=headers, json={"is_active": False}))
    assert api_client.get("/api/v1/me", headers=target_headers).status_code == 401
    assert (
        api_client.post(
            "/api/v1/auth/login",
            json={"email": "target@example.com", "password": "test-password-long"},
        ).status_code
        == 401
    )
    result(api_client.put(path + "/status", headers=headers, json={"is_active": True}))
    target_headers = login(api_client, "target")
    result(
        api_client.put(path + "/level", headers=headers, json={"level": "moderator"})
    )
    target_headers = login(api_client, "target")
    assert (
        api_client.get("/api/v1/admin/users", headers=target_headers).status_code == 403
    )
    assert (
        api_client.put(
            path + "/status", headers=target_headers, json={"is_active": False}
        ).status_code
        == 403
    )
    assert (
        api_client.put(
            f"/api/v1/admin/users/{admin['id']}/level",
            headers=headers,
            json={"level": "green"},
        ).status_code
        == 409
    )
    assert (
        api_client.put(
            f"/api/v1/admin/users/{admin['id']}/status",
            headers=headers,
            json={"is_active": False},
        ).status_code
        == 409
    )
    audit = result(api_client.get("/api/v1/admin/audit", headers=headers))
    assert any(
        item["action"] == "admin_user_experience_updated" for item in audit["items"]
    )
    assert (
        api_client.post(
            "/api/v1/auth/register",
            json={
                "email": "hack@example.com",
                "password": "test-password-long",
                "display_name": "Hack",
                "level": "admin",
            },
        ).status_code
        == 422
    )


def test_admin_profiles_private_playlists_and_audit_rollback(
    api_client, account, catalog_db, monkeypatch
):
    admin, headers = account("admin")
    target, own = account("target")
    set_role(catalog_db, admin, "admin")
    path = f"/api/v1/admin/users/{target['id']}"
    edited = result(
        api_client.patch(
            path, headers=headers, json={"display_name": "Changed", "bio": "Biography"}
        )
    )
    assert edited["display_name"] == "Changed" and "password_hash" not in edited

    def fail(*args, **kwargs):
        raise RuntimeError("Audit unavailable")

    import APP.services.admin as admin_service

    monkeypatch.setattr(admin_service, "record_event", fail)
    with pytest.raises(RuntimeError):
        api_client.put(path + "/level", headers=headers, json={"level": "moderator"})
    assert result(api_client.get("/api/v1/me", headers=own))["level"] == "green"
    playlist = result(
        api_client.post(
            "/api/v1/playlists",
            headers=own,
            json={"name": "Private", "visibility": "private"},
        ),
        201,
    )
    result(
        api_client.patch(
            f"/api/v1/playlists/{playlist['id']}",
            headers=headers,
            json={"name": "Corrected"},
        )
    )
    assert (
        result(api_client.get(f"/api/v1/playlists/{playlist['id']}", headers=own))[
            "name"
        ]
        == "Corrected"
    )
    liked = next(
        item
        for item in result(api_client.get("/api/v1/me/playlists", headers=own))["items"]
        if item["kind"] == "liked"
    )
    assert (
        api_client.patch(
            f"/api/v1/playlists/{liked['id']}", headers=headers, json={"name": "Hack"}
        ).status_code
        == 409
    )


@pytest.mark.parametrize(
    "level,points,allowed",
    [
        ("green", 0, False),
        ("experienced", 700, False),
        ("moderator", 0, True),
        ("admin", 0, True),
    ],
)
def test_foreign_content_editing(
    api_client, account, catalog_db, music, level, points, allowed
):
    _, _, artist, album, tracks = music
    user, headers = account("editor")
    set_role(catalog_db, user, level, points)
    assert api_client.patch(
        f"/api/v1/tracks/{tracks[0]['id']}", headers=headers, json={"lyrics": "Updated"}
    ).status_code == (200 if allowed else 403)
    assert api_client.patch(
        f"/api/v1/artists/{artist['id']}", headers=headers, json={"bio": "Updated"}
    ).status_code == (200 if allowed else 403)
    assert api_client.patch(
        f"/api/v1/albums/{album['id']}", headers=headers, json={"title": "Updated"}
    ).status_code == (200 if allowed else 403)


def test_developer_admin_creation_and_promotion(catalog_db):
    async def run():
        factory = async_sessionmaker(catalog_db.engine, expire_on_commit=False)
        async with factory() as session:
            user_id = await provision_admin(
                session,
                catalog_db.settings,
                RegisterInput(
                    email="developer@example.com",
                    display_name="Developer",
                    password="test-password-long",
                ),
            )
        async with factory() as session:
            assert (
                await provision_admin(
                    session, catalog_db.settings, promote_email="developer@example.com"
                )
                == user_id
            )
        return user_id

    user_id = asyncio.run(run())
    user = catalog_db.execute(
        "SELECT level,password_hash FROM users WHERE id=:id", {"id": user_id}
    )[0]
    assert user["level"] == "admin" and "test-password" not in user["password_hash"]
    assert (
        len(
            catalog_db.execute(
                "SELECT id FROM event_logs WHERE action='developer_admin_provisioned'"
            )
        )
        == 2
    )


def test_listening_time_uniqueness_cap_and_owner_exclusion(
    api_client, account, catalog_db, music
):
    owner, own, _, _, tracks = music
    playable(catalog_db, owner, tracks[0])
    playable(catalog_db, owner, tracks[1])
    listener, headers = account("listenerxp")
    assert (
        api_client.post(
            f"/api/v1/tracks/{tracks[0]['id']}/listening", headers=own
        ).status_code
        == 409
    )
    first = result(
        api_client.post(f"/api/v1/tracks/{tracks[0]['id']}/listening", headers=headers),
        201,
    )
    assert not result(
        api_client.put(
            f"/api/v1/listening/{first['id']}",
            headers=headers,
            json={"is_playing": True},
        )
    )["awarded"]
    assert (
        api_client.put(
            f"/api/v1/listening/{first['id']}", headers=own, json={"is_playing": True}
        ).status_code
        == 404
    )
    assert (
        api_client.put(
            f"/api/v1/listening/{first['id']}",
            headers=headers,
            json={"is_playing": True, "seconds": 100000},
        ).status_code
        == 422
    )
    api_client.app.state.settings.listen_daily_cap = 1
    outcome = credit_listen(api_client, catalog_db, headers, tracks[0]["id"])
    assert outcome["awarded"] and outcome["experience"]["experience_points"] == 1
    repeated = credit_listen(api_client, catalog_db, headers, tracks[0]["id"])
    assert not repeated["awarded"] and repeated["experience"]["experience_points"] == 1
    limited = credit_listen(api_client, catalog_db, headers, tracks[1]["id"])
    assert not limited["awarded"] and limited["experience"]["experience_points"] == 1


def test_quality_award_once_and_concurrent_claim(
    api_client, account, catalog_db, music
):
    owner, own, _, _, tracks = music
    playable(catalog_db, owner, tracks[0])
    for index in range(3):
        _, headers = account("raterxp" + str(index))
        result(
            api_client.put(
                "/api/v1/ratings",
                headers=headers,
                json={
                    "target_type": "track",
                    "target_id": tracks[0]["id"],
                    "value": 4.5,
                },
            )
        )
    assert (
        result(api_client.get("/api/v1/me/experience", headers=own))[
            "experience_points"
        ]
        == 20
    )

    async def run():
        factory = async_sessionmaker(catalog_db.engine, expire_on_commit=False)

        async def claim():
            async with factory() as session:
                return await claim_quality(
                    session, SimpleNamespace(id=owner["id"]), catalog_db.settings
                )

        return await asyncio.gather(claim(), claim())

    values = asyncio.run(run())
    assert [value.experience_points for value in values] == [20, 20]
    assert (
        len(catalog_db.execute("SELECT id FROM experience_awards WHERE kind='quality'"))
        == 1
    )


def test_contribution_moderation_isolation_stale_and_permissions(
    api_client, account, catalog_db, music
):
    owner, own, _, _, tracks = music
    genre_id = catalog_db.execute(
        "INSERT INTO genres(name,slug) VALUES ('Rock','rock') RETURNING id"
    )[0]["id"]
    user, headers = account("contributor")
    mod, moderation = account("mod")
    set_role(catalog_db, mod, "moderator")
    payload = {
        "target_type": "track",
        "target_id": tracks[0]["id"],
        "field": "lyrics",
        "lyrics": "Proposal",
    }
    set_role(catalog_db, user, "experienced", 100)
    proposal = result(
        api_client.post("/api/v1/contributions", headers=headers, json=payload), 201
    )
    assert result(api_client.get(f"/api/v1/tracks/{tracks[0]['id']}"))["lyrics"] is None
    assert (
        api_client.put(
            f"/api/v1/admin/contributions/{proposal['id']}",
            headers=headers,
            json={"decision": "approve"},
        ).status_code
        == 403
    )
    assert (
        result(api_client.get("/api/v1/me/contributions", headers=own))["items"] == []
    )
    result(
        api_client.put(
            f"/api/v1/admin/contributions/{proposal['id']}",
            headers=moderation,
            json={"decision": "approve"},
        )
    )
    assert (
        result(api_client.get(f"/api/v1/tracks/{tracks[0]['id']}"))["lyrics"]
        == "Proposal"
    )
    assert (
        api_client.put(
            f"/api/v1/admin/contributions/{proposal['id']}",
            headers=moderation,
            json={"decision": "approve"},
        ).status_code
        == 409
    )
    proposal = result(
        api_client.post(
            "/api/v1/contributions",
            headers=headers,
            json={**payload, "lyrics": "Second"},
        ),
        201,
    )
    result(
        api_client.patch(
            f"/api/v1/tracks/{tracks[0]['id']}",
            headers=own,
            json={"lyrics": "Owner update"},
        )
    )
    assert (
        api_client.put(
            f"/api/v1/admin/contributions/{proposal['id']}",
            headers=moderation,
            json={"decision": "approve"},
        ).status_code
        == 403
    )
    result(
        api_client.put(
            f"/api/v1/admin/contributions/{proposal['id']}",
            headers=moderation,
            json={"decision": "reject", "reason": "Запись изменена автором"},
        )
    )
    assert (
        result(api_client.get(f"/api/v1/tracks/{tracks[0]['id']}"))["lyrics"]
        == "Owner update"
    )
    genre_proposal = result(
        api_client.post(
            "/api/v1/contributions",
            headers=headers,
            json={
                "target_type": "track",
                "target_id": tracks[0]["id"],
                "field": "genres",
                "genre_ids": [genre_id],
            },
        ),
        201,
    )
    assert genre_proposal["status"] == "pending"
    assert (
        api_client.patch(
            f"/api/v1/tracks/{tracks[0]['id']}",
            headers=headers,
            json={"lyrics": "Bypass"},
        ).status_code
        == 403
    )


def test_contribution_concurrent_approval_and_pending_limit(
    api_client, account, catalog_db, music
):
    _, _, _, _, tracks = music
    genre_id = catalog_db.execute(
        "INSERT INTO genres(name,slug) VALUES ('Rock','rock') RETURNING id"
    )[0]["id"]
    user, headers = account("contributor")
    mod, moderation = account("mod")
    set_role(catalog_db, user, "experienced", 100)
    set_role(catalog_db, mod, "moderator")
    payload = {
        "target_type": "track",
        "target_id": tracks[0]["id"],
        "field": "lyrics",
        "lyrics": "Proposal",
    }
    proposal = result(
        api_client.post("/api/v1/contributions", headers=headers, json=payload), 201
    )

    def approve(_):
        return api_client.put(
            f"/api/v1/admin/contributions/{proposal['id']}",
            headers=moderation,
            json={"decision": "approve"},
        ).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(approve, range(2))) == [200, 409]
    for index, field in enumerate(("lyrics", "genres", "metadata")):
        result(
            api_client.post(
                "/api/v1/contributions",
                headers=headers,
                json={
                    "target_type": "track",
                    "target_id": tracks[0]["id"],
                    "field": field,
                    **(
                        {"lyrics": "Pending"}
                        if field == "lyrics"
                        else {"genre_ids": [genre_id]}
                        if field == "genres"
                        else {"name": "Corrected"}
                    ),
                },
            ),
            201,
        )
    assert (
        api_client.post(
            "/api/v1/contributions",
            headers=headers,
            json={**payload, "target_id": tracks[1]["id"], "lyrics": "Too many"},
        ).status_code
        == 409
    )
