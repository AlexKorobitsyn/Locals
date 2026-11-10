import asyncio

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker
from test_library import result

from APP.models import User
from APP.schemas.preferences import FavoriteGenresPut
from APP.services.preferences import replace_favorite_genres

pytestmark = pytest.mark.integration


@pytest.fixture
def catalogue(catalog_db):
    genres = {}
    for slug in ["jazz", "rock", "ambient"]:
        genres[slug] = catalog_db.execute(
            "INSERT INTO genres(name,slug) VALUES (:slug,:slug) RETURNING id",
            {"slug": slug},
        )[0]["id"]
    artist = catalog_db.execute(
        "INSERT INTO artists(name) VALUES ('Imported artist') RETURNING id"
    )[0]["id"]

    def track(title, genre_ids=(), album_id=None, user_id=None, artist_id=artist):
        track_id = catalog_db.execute(
            "INSERT INTO tracks(title,duration,album_id,user_id) VALUES (:title,120,:album,:user) RETURNING id",
            {"title": title, "album": album_id, "user": user_id},
        )[0]["id"]
        catalog_db.execute(
            "INSERT INTO track_artists(track_id,artist_id,role) VALUES (:track,:artist,'primary')",
            {"track": track_id, "artist": artist_id},
        )
        for genre_id in genre_ids:
            catalog_db.execute(
                "INSERT INTO track_genres(track_id,genre_id) VALUES (:track,:genre)",
                {"track": track_id, "genre": genre_id},
            )
        return track_id

    return genres, artist, track


def recommendations(client, headers=None, **params):
    return result(
        client.get("/api/v1/recommendations/tracks", headers=headers, params=params)
    )


def rate(client, headers, kind, target, value):
    return result(
        client.put(
            "/api/v1/ratings",
            headers=headers,
            json={"target_type": kind, "target_id": target, "value": value},
        )
    )


def test_empty_catalog_and_optional_auth(api_client, account):
    assert recommendations(api_client) == {
        "items": [],
        "total": 0,
        "limit": 20,
        "offset": 0,
        "mode": "popular",
        "algorithm_version": "rules_v1",
    }
    _, headers = account()
    assert recommendations(api_client, headers)["mode"] == "popular"
    assert (
        api_client.get(
            "/api/v1/recommendations/tracks",
            headers={"Authorization": "Bearer invalid"},
        ).status_code
        == 401
    )
    assert (
        api_client.get(
            "/api/v1/recommendations/tracks", params={"limit": 101}
        ).status_code
        == 422
    )
    assert (
        api_client.get(
            "/api/v1/recommendations/tracks", params={"offset": -1}
        ).status_code
        == 422
    )


def test_cold_start_quality_ranking_and_pagination(api_client, account, catalogue):
    genres, _, track = catalogue
    low = track("Low", [genres["jazz"]])
    high = track("High", [genres["rock"]])
    unknown = track("Unknown")
    _, voter = account("voter")
    rate(api_client, voter, "track", low, 1)
    rate(api_client, voter, "track", high, 5)
    page = recommendations(api_client, limit=2)
    assert [item["id"] for item in page["items"]] == [high, unknown]
    assert page["mode"] == "popular" and page["total"] == 3
    assert page["items"][0]["score"]["total"] == pytest.approx(
        ((5 + 50 * 3) / 51 - 1) / 4
    )
    assert "community_rating" in page["items"][0]["reasons"]
    tail = recommendations(api_client, limit=2, offset=2)
    assert [item["id"] for item in tail["items"]] == [low]
    beyond = recommendations(api_client, offset=100)
    assert beyond["items"] == [] and beyond["total"] == 3
    assert recommendations(api_client, playable_only=True)["total"] == 0


def test_public_average_and_recommendation_rank_are_independent(
    api_client, account, catalogue
):
    _, _, track = catalogue
    sparse = track("Three perfect ratings")
    established = track("Ten strong ratings")
    for index in range(10):
        _, voter = account(f"voter{index}")
        rate(api_client, voter, "track", established, 4.5)
        if index < 3:
            rate(api_client, voter, "track", sparse, 5)

    page = recommendations(api_client)
    assert [item["id"] for item in page["items"]] == [established, sparse]
    assert [item["rating_avg"] for item in page["items"]] == [4.5, 5]
    assert page["items"][0]["score"]["quality_score"] == pytest.approx(
        ((45 + 50 * 3) / 60 - 1) / 4
    )
    assert page["items"][1]["score"]["quality_score"] == pytest.approx(
        ((15 + 50 * 3) / 53 - 1) / 4
    )
    catalog = result(api_client.get("/api/v1/tracks?sort=-rating_avg"))
    assert [item["id"] for item in catalog["items"]] == [sparse, established]


def test_favorites_affinity_negative_feedback_and_isolation(
    api_client, account, catalogue
):
    genres, _, track = catalogue
    liked_jazz = track("Rated Jazz", [genres["jazz"]])
    disliked_rock = track("Rated Rock", [genres["rock"]])
    jazz = track("New jazz", [genres["jazz"]])
    rock = track("New rock", [genres["rock"]])
    ambient = track("New ambient", [genres["ambient"]])
    mixed = track("Jazz + rock", [genres["jazz"], genres["rock"]])
    _, user = account("listener")
    _, other = account("other")
    result(
        api_client.put(
            "/api/v1/me/favorite-genres",
            headers=user,
            json={"genre_ids": [genres["jazz"]]},
        )
    )
    rate(api_client, user, "track", liked_jazz, 5)
    rate(api_client, user, "track", disliked_rock, 1)
    page = recommendations(api_client, user)
    assert page["mode"] == "personalized"
    assert [item["id"] for item in page["items"]] == [jazz, mixed, ambient, rock]
    best = page["items"][0]
    assert best["score"] == {
        "favorite_genre_score": 2.0,
        "rated_genre_score": 2.0,
        "quality_score": 0.5,
        "total": 4.5,
    }
    assert best["matched_favorite_genres"][0]["id"] == genres["jazz"]
    assert best["genre_preferences"][0]["affinity"] == 2
    assert page["items"][-1]["score"]["rated_genre_score"] == -2
    assert "low_rated_genres" in page["items"][-1]["reasons"]
    assert page["items"][1]["score"]["favorite_genre_score"] == 1
    assert page["items"][1]["score"]["rated_genre_score"] == 0
    unrelated = recommendations(api_client, other)
    assert unrelated["mode"] == "popular"
    assert all(
        item["matched_favorite_genres"] == [] and item["genre_preferences"] == []
        for item in unrelated["items"]
    )
    for item in page["items"]:
        assert item["my_rating"] is None and item["is_liked_by_me"] is False
        assert "rating_sum" not in item and "rating_weight" not in item


def test_excludes_known_uploaded_and_owned_artist_tracks(
    api_client, account, catalogue, catalog_db
):
    _, _, track = catalogue
    user, headers = account("listener")
    rated = track("Rated")
    favorite = track("Favorite")
    track("Uploaded", user_id=user["id"])
    owned_artist = catalog_db.execute(
        "INSERT INTO artists(name,user_id) VALUES ('Own',:user) RETURNING id",
        {"user": user["id"]},
    )[0]["id"]
    track("Owned credit", artist_id=owned_artist)
    new = track("New")
    rate(api_client, headers, "track", rated, 3)
    result(
        api_client.put(
            "/api/v1/favorites",
            headers=headers,
            json={"entity_type": "track", "entity_id": favorite},
        )
    )
    assert [item["id"] for item in recommendations(api_client, headers)["items"]] == [
        new
    ]


def test_genre_fallback_and_album_artist_rating_signals(
    api_client, account, catalogue, catalog_db
):
    genres, artist, track = catalogue
    catalog_db.execute(
        "INSERT INTO artist_genres(artist_id,genre_id) VALUES (:artist,:genre)",
        {"artist": artist, "genre": genres["rock"]},
    )
    album = catalog_db.execute(
        "INSERT INTO albums(title) VALUES ('Jazz album') RETURNING id"
    )[0]["id"]
    catalog_db.execute(
        "INSERT INTO album_genres(album_id,genre_id) VALUES (:album,:genre)",
        {"album": album, "genre": genres["jazz"]},
    )
    inherited_album = track("From album", album_id=album)
    inherited_artist = track("From artist")
    explicit = track("Explicit", [genres["ambient"]], album_id=album)
    # Второй credit того же артиста не должен удваивать его вклад.
    catalog_db.execute(
        "INSERT INTO track_artists(track_id,artist_id,role) VALUES (:track,:artist,'vocals')",
        {"track": inherited_artist, "artist": artist},
    )
    _, headers = account()
    rate(api_client, headers, "album", album, 5)
    rate(api_client, headers, "artist", artist, 1)
    page = recommendations(api_client, headers)
    assert [item["id"] for item in page["items"]] == [
        inherited_album,
        explicit,
        inherited_artist,
    ]
    assert [item["genres"][0]["id"] for item in page["items"]] == [
        genres["jazz"],
        genres["ambient"],
        genres["rock"],
    ]
    assert page["items"][-1]["genre_preferences"][0]["ratings_count"] == 1


def test_preference_validation_idempotency_clear_and_private_audit(
    api_client, account, catalogue, catalog_db, monkeypatch
):
    genres, _, _ = catalogue
    user, headers = account()
    assert api_client.get("/api/v1/me/favorite-genres").status_code == 401
    assert (
        api_client.put(
            "/api/v1/me/favorite-genres", headers=headers, json={"genre_ids": [True]}
        ).status_code
        == 422
    )
    assert (
        api_client.put(
            "/api/v1/me/favorite-genres",
            headers=headers,
            json={"genre_ids": [genres["jazz"], genres["jazz"]]},
        ).status_code
        == 422
    )
    payload = {"genre_ids": [genres["jazz"]]}
    result(api_client.put("/api/v1/me/favorite-genres", headers=headers, json=payload))
    assert (
        result(api_client.get("/api/v1/me/favorite-genres", headers=headers))[0]["id"]
        == genres["jazz"]
    )
    result(api_client.put("/api/v1/me/favorite-genres", headers=headers, json=payload))
    assert (
        api_client.put(
            "/api/v1/me/favorite-genres", headers=headers, json={"genre_ids": [999999]}
        ).status_code
        == 404
    )
    assert (
        result(api_client.get("/api/v1/me/favorite-genres", headers=headers))[0]["id"]
        == genres["jazz"]
    )
    rows = catalog_db.execute(
        "SELECT is_public FROM event_logs WHERE action='favorite_genres_updated'"
    )
    assert len(rows) == 1 and rows[0]["is_public"] is False
    import APP.services.preferences as preferences

    def fail(*args, **kwargs):
        raise RuntimeError("audit unavailable")

    with monkeypatch.context() as scoped:
        scoped.setattr(preferences, "record_event", fail)
        with pytest.raises(RuntimeError):
            api_client.put(
                "/api/v1/me/favorite-genres",
                headers=headers,
                json={"genre_ids": [genres["rock"]]},
            )
    assert (
        result(api_client.get("/api/v1/me/favorite-genres", headers=headers))[0]["id"]
        == genres["jazz"]
    )
    result(
        api_client.put(
            "/api/v1/me/favorite-genres", headers=headers, json={"genre_ids": []}
        )
    )
    assert result(api_client.get("/api/v1/me/favorite-genres", headers=headers)) == []


def test_concurrent_preference_replacement_is_one_complete_set(
    api_client, account, catalogue, catalog_db
):
    genres, _, _ = catalogue
    user, _ = account()

    async def run():
        factory = async_sessionmaker(catalog_db.engine, expire_on_commit=False)

        async def replace(ids):
            async with factory() as session:
                return await replace_favorite_genres(
                    session, User(id=user["id"]), FavoriteGenresPut(genre_ids=ids)
                )

        await asyncio.wait_for(
            asyncio.gather(
                replace([genres["jazz"]]), replace([genres["rock"], genres["ambient"]])
            ),
            timeout=10,
        )

    asyncio.run(run())
    stored = {
        row["genre_id"]
        for row in catalog_db.execute("SELECT genre_id FROM user_favorite_genres")
    }
    assert stored in ({genres["jazz"]}, {genres["rock"], genres["ambient"]})
