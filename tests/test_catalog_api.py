import pytest
from sqlalchemy.exc import IntegrityError

pytestmark = pytest.mark.integration


def create(client, path, headers, payload):
    response = client.post("/api/v1/" + path, headers=headers, json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_catalog_creation_details_and_credits(api_client, account, catalog_db):
    user, headers = account()
    catalog_db.execute(
        "UPDATE users SET level='experienced' WHERE id=:id", {"id": user["id"]}
    )
    genre = create(api_client, "genres", headers, {"name": "Jazz", "slug": "jazz"})
    artist = create(
        api_client, "artists", headers, {"name": "  Solo  ", "genre_ids": [genre["id"]]}
    )
    assert (
        artist["name"] == "Solo"
        and artist["user_id"] == user["id"]
        and artist["is_owner"]
    )
    assert artist["rating_avg"] is None and artist["genres"][0]["slug"] == "jazz"
    album = create(
        api_client,
        "albums",
        headers,
        {
            "title": "Album",
            "artist_ids": [artist["id"]],
            "genre_ids": [genre["id"]],
            "release_date": "2026-01-01",
        },
    )
    track = create(
        api_client,
        "tracks",
        headers,
        {
            "title": "Track",
            "duration": 123,
            "album_id": album["id"],
            "genre_ids": [genre["id"]],
            "artist_credits": [
                {"artist_id": artist["id"], "role": "guitar"},
                {"artist_id": artist["id"], "role": "vocals"},
            ],
        },
    )
    assert track["album"]["id"] == album["id"] and len(track["artists"]) == 1
    assert {credit["role"] for credit in track["artist_credits"]} == {
        "guitar",
        "vocals",
    }
    assert track["genres"][0]["id"] == genre["id"]
    artist_detail = api_client.get(f"/api/v1/artists/{artist['id']}").json()
    assert artist_detail["albums_count"] == artist_detail["tracks_count"] == 1
    assert not artist_detail["is_owner"]
    album_detail = api_client.get(f"/api/v1/albums/{album['id']}").json()
    assert album_detail["tracks_count"] == 1 and album_detail["duration"] == 123
    assert api_client.get("/api/v1/me", headers=headers).json()["type"] == "artist"
    events = catalog_db.execute("SELECT action FROM event_logs WHERE is_public=true")
    assert {event["action"] for event in events} == {
        "genre_created",
        "artist_created",
        "album_created",
        "track_created",
    }


def test_catalog_ownership_and_missing_references(api_client, account, catalog_db):
    owner, headers = account("owner")
    other, other_headers = account("other")
    artist = create(api_client, "artists", headers, {"name": "Owned"})
    album = create(
        api_client, "albums", headers, {"title": "Owned", "artist_ids": [artist["id"]]}
    )
    own_other_artist = create(api_client, "artists", other_headers, {"name": "Other"})
    assert (
        api_client.post("/api/v1/artists", json={"name": "Anonymous"}).status_code
        == 401
    )
    for level in ("green", "admin"):
        catalog_db.execute(
            "UPDATE users SET level=:level WHERE id=:id",
            {"level": level, "id": other["id"]},
        )
        assert (
            api_client.patch(
                f"/api/v1/artists/{artist['id']}",
                headers=other_headers,
                json={"name": "Hijack"},
            ).status_code
            == 403
        )
        assert (
            api_client.post(
                "/api/v1/albums",
                headers=other_headers,
                json={"title": "Hijack", "artist_ids": [artist["id"]]},
            ).status_code
            == 403
        )
        assert (
            api_client.post(
                "/api/v1/tracks",
                headers=other_headers,
                json={
                    "title": "Hijack",
                    "duration": 10,
                    "album_id": album["id"],
                    "artist_ids": [own_other_artist["id"]],
                },
            ).status_code
            == 403
        )
    assert (
        api_client.post(
            "/api/v1/artists",
            headers=headers,
            json={"name": "Missing", "city_id": 99999},
        ).status_code
        == 404
    )
    assert (
        api_client.post(
            "/api/v1/artists",
            headers=headers,
            json={"name": "Missing", "genre_ids": [99999]},
        ).status_code
        == 404
    )
    assert (
        api_client.post(
            "/api/v1/albums",
            headers=headers,
            json={"title": "Missing", "artist_ids": [99999]},
        ).status_code
        == 404
    )
    assert (
        api_client.post(
            "/api/v1/tracks",
            headers=headers,
            json={
                "title": "Missing",
                "duration": 10,
                "artist_ids": [artist["id"]],
                "album_id": 99999,
            },
        ).status_code
        == 404
    )
    assert api_client.get("/api/v1/tracks/99999").status_code == 404
    assert (
        api_client.post(
            "/api/v1/artists",
            headers=headers,
            json={"name": "Hijack", "user_id": other["id"]},
        ).status_code
        == 422
    )


def test_patch_relations_and_nullable_fields(api_client, account, catalog_db):
    _, headers = account()
    artist = create(api_client, "artists", headers, {"name": "A", "bio": "Bio"})
    album = create(
        api_client, "albums", headers, {"title": "A", "artist_ids": [artist["id"]]}
    )
    track = create(
        api_client,
        "tracks",
        headers,
        {
            "title": "A",
            "duration": 90,
            "artist_ids": [artist["id"]],
            "album_id": album["id"],
        },
    )
    response = api_client.patch(
        f"/api/v1/tracks/{track['id']}",
        headers=headers,
        json={
            "title": "B",
            "duration": 100,
            "album_id": None,
            "artist_credits": [{"artist_id": artist["id"], "role": "guitar"}],
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["album"] is None and response.json()["duration"] == 100
    assert response.json()["artist_credits"][0]["role"] == "guitar"
    # Повторная роль заменяет связь без конфликта первичного ключа.
    again = api_client.patch(
        f"/api/v1/tracks/{track['id']}",
        headers=headers,
        json={"artist_credits": [{"artist_id": artist["id"], "role": "guitar"}]},
    )
    assert again.status_code == 200, again.text
    assert (
        api_client.patch(
            f"/api/v1/artists/{artist['id']}", headers=headers, json={"bio": None}
        ).json()["bio"]
        is None
    )
    assert api_client.get(f"/api/v1/albums/{album['id']}").json()["tracks_count"] == 0
    failed = api_client.patch(
        f"/api/v1/tracks/{track['id']}",
        headers=headers,
        json={"title": "Rollback", "artist_ids": [99999]},
    )
    assert failed.status_code == 404
    unchanged = api_client.get(f"/api/v1/tracks/{track['id']}").json()
    assert (
        unchanged["title"] == "B" and unchanged["artist_credits"][0]["role"] == "guitar"
    )
    assert (
        catalog_db.execute("SELECT count(*) AS count FROM track_artists")[0]["count"]
        == 1
    )


def test_pages_sorting_filters_and_validation(api_client, account):
    _, headers = account()
    artists = [
        create(api_client, "artists", headers, {"name": name})
        for name in ("C", "A", "B", "B")
    ]
    page = api_client.get("/api/v1/artists?sort=name&limit=2&offset=1").json()
    assert page["total"] == 4 and [row["name"] for row in page["items"]] == ["B", "B"]
    assert [row["id"] for row in page["items"]] == sorted(
        row["id"] for row in page["items"]
    )
    assert api_client.get("/api/v1/artists?offset=100").json()["total"] == 4
    assert api_client.get("/api/v1/artists?offset=100").json()["items"] == []
    assert api_client.get("/api/v1/artists?sort=-createdAt").status_code == 200
    for query in (
        "limit=0",
        "limit=101",
        "offset=-1",
        "sort=password_hash",
        "sort=name;DROP TABLE users",
        "sort=--name",
    ):
        assert api_client.get("/api/v1/artists?" + query).status_code == 422
    assert api_client.get("/api/v1/artists/0").status_code == 422
    assert (
        api_client.get(
            "/api/v1/artists", headers={"Authorization": "Bearer invalid"}
        ).status_code
        == 401
    )
    album = create(
        api_client,
        "albums",
        headers,
        {"title": "Release", "artist_ids": [artists[0]["id"]]},
    )
    track = create(
        api_client,
        "tracks",
        headers,
        {
            "title": "Track",
            "duration": 10,
            "artist_ids": [artists[0]["id"]],
            "album_id": album["id"],
        },
    )
    assert (
        api_client.get(f"/api/v1/albums?artist_id={artists[0]['id']}").json()["items"][
            0
        ]["id"]
        == album["id"]
    )
    assert (
        api_client.get(
            f"/api/v1/tracks?artist_id={artists[0]['id']}&album_id={album['id']}"
        ).json()["items"][0]["id"]
        == track["id"]
    )
    assert (
        api_client.get(f"/api/v1/tracks?artist_id={artists[1]['id']}").json()["items"]
        == []
    )


def test_genre_privileges_uniqueness_and_empty_artist_validation(
    api_client, account, catalog_db
):
    user, headers = account()
    assert (
        api_client.post(
            "/api/v1/genres", headers=headers, json={"slug": "jazz", "name": "Jazz"}
        ).status_code
        == 403
    )
    catalog_db.execute(
        "UPDATE users SET level='experienced' WHERE id=:id", {"id": user["id"]}
    )
    create(api_client, "genres", headers, {"slug": "jazz", "name": "Jazz"})
    assert (
        api_client.post(
            "/api/v1/genres", headers=headers, json={"slug": "jazz", "name": "Jazz"}
        ).status_code
        == 409
    )
    assert api_client.get("/api/v1/genres").json()["total"] == 1
    for path, payload in [
        ("albums", {"title": "Empty", "artist_ids": []}),
        ("tracks", {"title": "Empty", "duration": 10}),
    ]:
        assert (
            api_client.post(
                "/api/v1/" + path, headers=headers, json=payload
            ).status_code
            == 422
        )


def test_catalog_audit_failure_rolls_back_creation(api_client, account, catalog_db):
    _, headers = account()
    catalog_db.execute(
        "ALTER TABLE event_logs ADD CONSTRAINT reject_artist_event CHECK (action <> 'artist_created')"
    )
    with pytest.raises(IntegrityError):
        api_client.post("/api/v1/artists", headers=headers, json={"name": "Rollback"})
    assert catalog_db.execute("SELECT count(*) AS count FROM artists")[0]["count"] == 0
