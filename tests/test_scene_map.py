import pytest
from test_library import result

pytestmark = pytest.mark.integration


def test_map_uses_live_venue_location_and_filters_its_events(
    api_client, account, catalog_db
):
    user, headers = account("organizer")
    catalog_db.execute(
        "UPDATE users SET scene_verified=true WHERE id=:id", {"id": user["id"]}
    )
    city = catalog_db.execute(
        "INSERT INTO cities(name,country,lat,lng,timezone) VALUES ('Map City','RU',56,60,'Asia/Yekaterinburg') RETURNING id"
    )[0]["id"]
    city_response = result(api_client.get(f"/api/v1/cities/{city}"))
    assert city_response["lat"] == 56
    assert api_client.get(f"/api/v1/cities/{city + 100}").status_code == 404
    venue = result(
        api_client.post(
            "/api/v1/venues",
            headers=headers,
            json={"name": "Club", "city_id": city, "lat": 56.1, "lng": 60.2},
        ),
        201,
    )
    event = result(
        api_client.post(
            "/api/v1/events",
            headers=headers,
            json={
                "name": "Concert",
                "venue_id": venue["id"],
                "starts_at": "2027-06-01T18:00:00Z",
            },
        ),
        201,
    )
    result(
        api_client.post(
            "/api/v1/events",
            headers=headers,
            json={
                "name": "Open air",
                "city_id": city,
                "lat": 57,
                "lng": 61,
                "starts_at": "2027-06-01T18:00:00Z",
            },
        ),
        201,
    )
    page = result(api_client.get("/api/v1/events", params={"venue_id": venue["id"]}))
    assert page["total"] == 1 and page["items"][0]["id"] == event["id"]
    places = result(api_client.get("/api/v1/venues"))["items"]
    assert places[0]["lat"] == 56.1 and places[0]["lng"] == 60.2
    result(
        api_client.patch(
            f"/api/v1/venues/{venue['id']}",
            headers=headers,
            json={"lat": 58, "lng": 62},
        )
    )
    moved = result(api_client.get(f"/api/v1/events/{event['id']}"))
    assert (moved["lat"], moved["lng"]) == (58, 62)
    box = {"min_lat": 57.9, "max_lat": 58.1, "min_lng": 61.9, "max_lng": 62.1}
    assert result(api_client.get("/api/v1/events", params=box))["total"] == 1
    old_box = {"min_lat": 56, "max_lat": 56.2, "min_lng": 60, "max_lng": 60.3}
    assert result(api_client.get("/api/v1/events", params=old_box))["total"] == 0
    assert (
        result(
            api_client.get("/api/v1/events", params={"venue_id": venue["id"] + 100})
        )["total"]
        == 0
    )
    assert api_client.get("/api/v1/events?venue_id=0").status_code == 422


def test_map_excludes_unpublished_venues_and_events(api_client, account, catalog_db):
    _, headers = account("newcomer")
    city = catalog_db.execute(
        "INSERT INTO cities(name,country,lat,lng,timezone) VALUES ('City','RU',56,60,'Asia/Yekaterinburg') RETURNING id"
    )[0]["id"]
    venue = result(
        api_client.post(
            "/api/v1/venues",
            headers=headers,
            json={"name": "Pending club", "city_id": city, "lat": 56.1, "lng": 60.2},
        ),
        201,
    )
    result(
        api_client.post(
            "/api/v1/events",
            headers=headers,
            json={
                "name": "Pending event",
                "venue_id": venue["id"],
                "starts_at": "2027-06-01T18:00:00Z",
            },
        ),
        201,
    )
    box = {"min_lat": 56, "max_lat": 57, "min_lng": 60, "max_lng": 61}
    assert result(api_client.get("/api/v1/venues", params=box))["total"] == 0
    assert result(api_client.get("/api/v1/events", params=box))["total"] == 0
