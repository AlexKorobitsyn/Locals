import asyncio

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker
from test_library import favorite, result
from test_library import music as music

from APP.models import User
from APP.services.social import set_follow

pytestmark = pytest.mark.integration


@pytest.fixture
def city(catalog_db):
    return catalog_db.execute(
        "INSERT INTO cities(name,country,lat,lng,timezone) VALUES ('City','Country',56,60,'Asia/Yekaterinburg') RETURNING id"
    )[0]["id"]


def venue(client, headers, city_id):
    return result(
        client.post(
            "/api/v1/venues",
            headers=headers,
            json={"name": "Club", "city_id": city_id, "lat": 56.1, "lng": 60.2},
        ),
        201,
    )


def test_venue_rating_and_event_location_permissions(
    api_client, music, account, city, catalog_db
):
    owner, headers, _, _, _ = music
    catalog_db.execute(
        "UPDATE users SET scene_verified=true WHERE id=:id", {"id": owner["id"]}
    )
    _, other = account("other")
    place = venue(api_client, headers, city)
    assert place["is_owner"]
    assert (
        api_client.patch(
            f"/api/v1/venues/{place['id']}", headers=other, json={"name": "Other"}
        ).status_code
        == 403
    )
    result(
        api_client.put(
            "/api/v1/ratings",
            headers=other,
            json={"target_type": "venue", "target_id": place["id"], "value": 4.5},
        )
    )
    assert (
        result(api_client.get(f"/api/v1/venues/{place['id']}", headers=other))[
            "my_rating"
        ]
        == 4.5
    )
    favorite(api_client, other, "venue", place["id"])
    result(
        api_client.put(
            "/api/v1/follows",
            headers=other,
            json={"target_type": "venue", "target_id": place["id"]},
        )
    )
    detail = result(api_client.get(f"/api/v1/venues/{place['id']}", headers=other))
    assert (
        detail["likes_count"] == 1
        and detail["is_liked_by_me"]
        and detail["is_followed_by_me"]
    )
    payload = {
        "name": "Jam night",
        "venue_id": place["id"],
        "starts_at": "2026-11-01T18:00:00+05:00",
        "stop_at": "2026-11-01T20:00:00+05:00",
        "type_event_ids": [2],
    }
    event = result(
        api_client.post("/api/v1/events", headers=headers, json=payload), 201
    )
    assert event["city"]["id"] == city and event["lat"] == 56.1 and event["lng"] == 60.2
    assert event["type_event"][0]["slug"] == "jam"
    assert result(api_client.get(f"/api/v1/venues/{place['id']}"))["events_count"] == 1
    path = f"/api/v1/events/{event['id']}"
    assert (
        api_client.patch(path, headers=other, json={"name": "stolen"}).status_code
        == 403
    )
    assert (
        api_client.patch(
            path, headers=headers, json={"stop_at": "2026-11-01T10:00:00Z"}
        ).status_code
        == 422
    )
    assert api_client.get("/api/v1/events", params={"min_lat": 55}).status_code == 422
    box = {
        "city_id": city,
        "min_lat": 56,
        "max_lat": 57,
        "min_lng": 60,
        "max_lng": 61,
        "type_event_id": 2,
        "starts_after": "2026-11-01T12:00:00Z",
    }
    assert result(api_client.get("/api/v1/events", params=box))["total"] == 1
    assert (
        result(api_client.get("/api/v1/events", params={"city_id": city + 100}))[
            "total"
        ]
        == 0
    )
    assert (
        api_client.get(
            "/api/v1/events", params={"starts_after": "2026-11-01T12:00:00"}
        ).status_code
        == 422
    )
    result(
        api_client.patch(
            path, headers=headers, json={"venue_id": None, "lat": 55.8, "lng": 60.7}
        )
    )
    detached = result(api_client.get(path))
    assert detached["venue"] is None and detached["lat"] == 55.8
    favorite(api_client, other, "event", event["id"])
    result(api_client.delete(path, headers=headers), 204)
    assert api_client.get(path).status_code == 404
    assert (
        catalog_db.execute(
            "SELECT count(*) AS n FROM favorites WHERE entity_type='event'"
        )[0]["n"]
        == 0
    )


def test_event_city_defaults_types_and_validation(
    api_client, account, city, catalog_db
):
    owner, headers = account()
    catalog_db.execute(
        "UPDATE users SET scene_verified=true WHERE id=:id", {"id": owner["id"]}
    )
    event = result(
        api_client.post(
            "/api/v1/events",
            headers=headers,
            json={
                "name": "Concert",
                "city_id": city,
                "starts_at": "2026-11-01T18:00:00Z",
            },
        ),
        201,
    )
    assert (
        event["lat"] == 56
        and event["lng"] == 60
        and event["type_event"][0]["slug"] == "concert"
    )
    types = result(api_client.get("/api/v1/event-types"))
    assert [item["slug"] for item in types] == ["concert", "jam", "find_a_group"]
    assert (
        api_client.post(
            "/api/v1/events",
            headers=headers,
            json={"name": "No location", "starts_at": "2026-11-01T18:00:00Z"},
        ).status_code
        == 422
    )
    assert (
        api_client.patch(
            f"/api/v1/events/{event['id']}",
            headers=headers,
            json={"type_event_ids": []},
        ).status_code
        == 422
    )
    assert (
        api_client.get("/api/v1/events", params={"sort": "password_hash"}).status_code
        == 422
    )


def test_city_creation_privileged_search_timezone(api_client, account, catalog_db):
    user, headers = account()
    payload = {
        "name": "100% City",
        "country": "Country",
        "lat": 56,
        "lng": 60,
        "timezone": "Asia/Yekaterinburg",
    }
    assert (
        api_client.post("/api/v1/cities", headers=headers, json=payload).status_code
        == 403
    )
    catalog_db.execute(
        "UPDATE users SET level='moderator' WHERE id=:id", {"id": user["id"]}
    )
    result(api_client.post("/api/v1/cities", headers=headers, json=payload), 201)
    assert result(api_client.get("/api/v1/cities", params={"q": "100%"}))["total"] == 1
    assert (
        api_client.post(
            "/api/v1/cities",
            headers=headers,
            json={**payload, "timezone": "Invalid/Zone"},
        ).status_code
        == 422
    )


def test_artist_follow_feed_and_private_playlist_redaction(
    api_client, music, account, catalog_db
):
    musician, headers, artist, _, tracks = music
    _, follower = account("follower")
    result(
        api_client.put(
            "/api/v1/follows",
            headers=follower,
            json={"target_type": "artist", "target_id": artist["id"]},
        )
    )
    result(
        api_client.put(
            "/api/v1/follows",
            headers=follower,
            json={"target_type": "artist", "target_id": artist["id"]},
        )
    )
    assert (
        result(api_client.get("/api/v1/me/following", headers=follower))["total"] == 1
    )
    detail = result(api_client.get(f"/api/v1/artists/{artist['id']}", headers=follower))
    assert detail["followers_count"] == 1 and detail["is_followed_by_me"]
    playlist = result(
        api_client.post(
            "/api/v1/playlists", headers=headers, json={"name": "Private mix"}
        ),
        201,
    )
    favorite(api_client, headers, "track", tracks[0]["id"])
    feed = result(api_client.get("/api/v1/me/feed", headers=follower))
    assert any(item["action"] == "track_created" for item in feed["items"])
    assert not any(item["target_type"] == "playlist" for item in feed["items"])
    assert not any(item["action"].startswith("user_") for item in feed["items"])
    result(
        api_client.put(
            "/api/v1/follows",
            headers=follower,
            json={"target_type": "user", "target_id": musician["id"]},
        )
    )
    result(
        api_client.patch(
            f"/api/v1/playlists/{playlist['id']}",
            headers=headers,
            json={"visibility": "public"},
        )
    )
    assert any(
        item["target_type"] == "playlist"
        for item in result(api_client.get("/api/v1/me/feed", headers=follower))["items"]
    )
    result(
        api_client.patch(
            f"/api/v1/playlists/{playlist['id']}",
            headers=headers,
            json={"visibility": "private"},
        )
    )
    assert not any(
        item["target_type"] == "playlist"
        for item in result(api_client.get("/api/v1/me/feed", headers=follower))["items"]
    )
    result(
        api_client.delete(f"/api/v1/follows/artist/{artist['id']}", headers=follower),
        204,
    )
    result(
        api_client.delete(f"/api/v1/follows/user/{musician['id']}", headers=follower),
        204,
    )
    assert result(api_client.get("/api/v1/me/feed", headers=follower))["total"] == 0


def test_follow_rejects_self_and_missing_and_cross_follow_concurrency(
    api_client, account, catalog_db
):
    first, first_headers = account("first")
    second, _ = account("second")
    assert (
        api_client.put(
            "/api/v1/follows",
            headers=first_headers,
            json={"target_type": "user", "target_id": first["id"]},
        ).status_code
        == 409
    )
    assert (
        api_client.put(
            "/api/v1/follows",
            headers=first_headers,
            json={"target_type": "user", "target_id": 999999},
        ).status_code
        == 404
    )

    async def run():
        factory = async_sessionmaker(catalog_db.engine, expire_on_commit=False)

        async def follow(a, b):
            async with factory() as session:
                await set_follow(session, User(id=a), "user", b)

        await asyncio.wait_for(
            asyncio.gather(
                follow(first["id"], second["id"]), follow(second["id"], first["id"])
            ),
            timeout=10,
        )

    asyncio.run(run())
    assert catalog_db.execute("SELECT count(*) AS n FROM follows")[0]["n"] == 2
