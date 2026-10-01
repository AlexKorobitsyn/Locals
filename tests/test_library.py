import asyncio

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from APP.models import User
from APP.schemas.playlist import PlaylistTrackAdd
from APP.services.library import change_tracks, set_favorite

pytestmark = pytest.mark.integration


def result(response, code=200):
    assert response.status_code == code, response.text
    return response.json() if response.content else None


@pytest.fixture
def music(api_client, account):
    user, headers = account("musician")
    artist = result(
        api_client.post("/api/v1/artists", headers=headers, json={"name": "Artist"}),
        201,
    )
    album = result(
        api_client.post(
            "/api/v1/albums",
            headers=headers,
            json={"title": "Album", "artist_ids": [artist["id"]]},
        ),
        201,
    )
    tracks = [
        result(
            api_client.post(
                "/api/v1/tracks",
                headers=headers,
                json={
                    "title": f"Track {index}",
                    "duration": 20,
                    "artist_ids": [artist["id"]],
                    "album_id": album["id"],
                },
            ),
            201,
        )
        for index in range(3)
    ]
    return user, headers, artist, album, tracks


def rate(client, headers, track_id, value=4):
    return result(
        client.put(
            "/api/v1/ratings",
            headers=headers,
            json={"target_type": "track", "target_id": track_id, "value": value},
        )
    )


def favorite(client, headers, kind, entity_id):
    return result(
        client.put(
            "/api/v1/favorites",
            headers=headers,
            json={"entity_type": kind, "entity_id": entity_id},
        )
    )


def test_review_uses_current_rating_and_cascades(
    api_client, music, account, catalog_db
):
    _, headers, _, _, tracks = music
    _, other = account("other")
    target = tracks[0]["id"]
    payload = {"target_type": "track", "target_id": target, "text": "A review"}
    assert (
        api_client.post("/api/v1/reviews", headers=headers, json=payload).status_code
        == 409
    )
    rate(api_client, headers, target)
    review = result(
        api_client.post("/api/v1/reviews", headers=headers, json=payload), 201
    )
    assert review["rating"] == 4 and review["is_owner"]
    assert (
        api_client.post("/api/v1/reviews", headers=headers, json=payload).status_code
        == 409
    )
    assert (
        api_client.patch(
            f"/api/v1/reviews/{review['id']}", headers=other, json={"text": "changed"}
        ).status_code
        == 403
    )
    rate(api_client, headers, target, 2.5)
    assert result(api_client.get(f"/api/v1/reviews/{review['id']}"))["rating"] == 2.5
    favorite(api_client, other, "review", review["id"])
    liked = result(api_client.get(f"/api/v1/reviews/{review['id']}", headers=other))
    assert liked["likes_count"] == 1 and liked["is_liked_by_me"]
    assert (
        result(
            api_client.get(
                "/api/v1/reviews", params={"target_type": "track", "target_id": target}
            )
        )["total"]
        == 1
    )
    result(api_client.delete(f"/api/v1/ratings/track/{target}", headers=headers))
    assert api_client.get(f"/api/v1/reviews/{review['id']}").status_code == 404
    assert catalog_db.execute("SELECT count(*) AS n FROM reviews")[0]["n"] == 0
    assert (
        catalog_db.execute(
            "SELECT count(*) AS n FROM favorites WHERE entity_type='review'"
        )[0]["n"]
        == 0
    )
    assert result(api_client.get(f"/api/v1/tracks/{target}"))["ratings_count"] == 0


def test_delete_review_keeps_rating(api_client, music):
    _, headers, _, _, tracks = music
    target = tracks[0]["id"]
    rate(api_client, headers, target)
    review = result(
        api_client.post(
            "/api/v1/reviews",
            headers=headers,
            json={"target_type": "track", "target_id": target, "text": "text"},
        ),
        201,
    )
    result(api_client.delete(f"/api/v1/reviews/{review['id']}", headers=headers), 204)
    assert (
        result(api_client.get(f"/api/v1/tracks/{target}", headers=headers))["my_rating"]
        == 4
    )


def test_liked_single_source_private_immutable(api_client, music, account, catalog_db):
    user, headers, artist, album, tracks = music
    _, other = account("other")
    own = result(api_client.get("/api/v1/me/playlists", headers=headers))
    liked = next(item for item in own["items"] if item["kind"] == "liked")
    assert liked["tracks_count"] == 0
    for track in tracks:
        favorite(api_client, headers, "track", track["id"])
    duplicate = favorite(api_client, headers, "track", tracks[-1]["id"])
    assert (
        catalog_db.execute(
            "SELECT count(*) AS n FROM favorites WHERE user_id=:id", {"id": user["id"]}
        )[0]["n"]
        == 3
    )
    items = result(
        api_client.get(
            f"/api/v1/playlists/{liked['id']}/tracks",
            headers=headers,
            params={"limit": 2, "offset": 1},
        )
    )
    assert items["total"] == 3
    assert [item["track"]["id"] for item in items["items"]] == [
        tracks[1]["id"],
        tracks[0]["id"],
    ]
    assert [item["position"] for item in items["items"]] == [1, 2]
    assert all(item["track"]["is_liked_by_me"] for item in items["items"])
    assert catalog_db.execute("SELECT count(*) AS n FROM playlist_tracks")[0]["n"] == 0
    assert (
        api_client.get(f"/api/v1/playlists/{liked['id']}", headers=other).status_code
        == 404
    )
    assert api_client.get(f"/api/v1/playlists/{liked['id']}/tracks").status_code == 404
    assert (
        api_client.patch(
            f"/api/v1/playlists/{liked['id']}", headers=headers, json={"name": "other"}
        ).status_code
        == 409
    )
    assert (
        api_client.post(
            f"/api/v1/playlists/{liked['id']}/tracks",
            headers=headers,
            json={"track_id": tracks[0]["id"]},
        ).status_code
        == 409
    )
    assert (
        api_client.delete(
            f"/api/v1/playlists/{liked['id']}", headers=headers
        ).status_code
        == 409
    )
    assert (
        api_client.put(
            "/api/v1/favorites",
            headers=headers,
            json={"entity_type": "playlist", "entity_id": liked["id"]},
        ).status_code
        == 409
    )
    result(
        api_client.delete(
            f"/api/v1/favorites/track/{tracks[-1]['id']}", headers=headers
        ),
        204,
    )
    assert (
        result(api_client.get(f"/api/v1/playlists/{liked['id']}", headers=headers))[
            "tracks_count"
        ]
        == 2
    )
    result(
        api_client.delete(
            f"/api/v1/favorites/track/{tracks[-1]['id']}", headers=headers
        ),
        204,
    )
    favorite(api_client, headers, "album", album["id"])
    favorite(api_client, headers, "artist", artist["id"])
    for kind, entity in [("albums", album), ("artists", artist)]:
        assert result(
            api_client.get(f"/api/v1/{kind}/{entity['id']}", headers=headers)
        )["is_liked_by_me"]
        assert any(
            item["is_liked_by_me"]
            for item in result(api_client.get(f"/api/v1/{kind}", headers=headers))[
                "items"
            ]
        )
    assert duplicate["entity_type"] == "track"


def test_playlist_order_saving_and_visibility(api_client, music, account):
    _, headers, _, _, tracks = music
    _, other = account("other")
    playlist = result(
        api_client.post(
            "/api/v1/playlists",
            headers=headers,
            json={"name": "Mix", "visibility": "public"},
        ),
        201,
    )
    path = f"/api/v1/playlists/{playlist['id']}"
    assert "tracks" not in playlist
    for index in [0, 1]:
        result(
            api_client.post(
                path + "/tracks",
                headers=headers,
                json={"track_id": tracks[index]["id"]},
            ),
            204,
        )
    result(
        api_client.post(
            path + "/tracks",
            headers=headers,
            json={"track_id": tracks[2]["id"], "position": 1},
        ),
        204,
    )
    assert [
        item["track"]["id"]
        for item in result(api_client.get(path + "/tracks"))["items"]
    ] == [tracks[0]["id"], tracks[2]["id"], tracks[1]["id"]]
    assert (
        api_client.post(
            path + "/tracks", headers=headers, json={"track_id": tracks[0]["id"]}
        ).status_code
        == 409
    )
    assert (
        api_client.put(
            path + "/tracks/order",
            headers=headers,
            json={"track_ids": [tracks[0]["id"]]},
        ).status_code
        == 409
    )
    reordered = [item["id"] for item in reversed(tracks)]
    result(
        api_client.put(
            path + "/tracks/order", headers=headers, json={"track_ids": reordered}
        ),
        204,
    )
    assert [
        item["track"]["id"]
        for item in result(api_client.get(path + "/tracks"))["items"]
    ] == reordered
    result(api_client.delete(path + f"/tracks/{tracks[1]['id']}", headers=headers), 204)
    assert [
        item["position"] for item in result(api_client.get(path + "/tracks"))["items"]
    ] == [0, 1]
    assert (
        api_client.post(
            path + "/tracks", headers=other, json={"track_id": tracks[1]["id"]}
        ).status_code
        == 403
    )
    favorite(api_client, other, "playlist", playlist["id"])
    assert (
        result(api_client.get("/api/v1/me/saved-playlists", headers=other))["total"]
        == 1
    )
    result(api_client.patch(path, headers=headers, json={"visibility": "private"}))
    assert api_client.get(path, headers=other).status_code == 404
    assert (
        result(api_client.get("/api/v1/me/saved-playlists", headers=other))["total"]
        == 0
    )
    assert result(api_client.get("/api/v1/me/favorites", headers=other))["total"] == 0
    result(
        api_client.delete(
            f"/api/v1/favorites/playlist/{playlist['id']}", headers=other
        ),
        204,
    )
    result(api_client.delete(path, headers=headers), 204)
    assert api_client.get(path, headers=headers).status_code == 404


def test_review_and_playlist_audit_failure_rolls_back(
    api_client, music, catalog_db, monkeypatch
):
    import APP.services.library as library
    import APP.services.reviews as reviews

    _, headers, _, _, tracks = music
    rate(api_client, headers, tracks[0]["id"])

    def fail(*args, **kwargs):
        raise RuntimeError("audit unavailable")

    monkeypatch.setattr(reviews, "record_event", fail)
    with pytest.raises(RuntimeError):
        api_client.post(
            "/api/v1/reviews",
            headers=headers,
            json={"target_type": "track", "target_id": tracks[0]["id"], "text": "text"},
        )
    assert catalog_db.execute("SELECT count(*) AS n FROM reviews")[0]["n"] == 0
    monkeypatch.setattr(library, "record_event", fail)
    with pytest.raises(RuntimeError):
        api_client.put(
            "/api/v1/favorites",
            headers=headers,
            json={"entity_type": "track", "entity_id": tracks[0]["id"]},
        )
    assert catalog_db.execute("SELECT count(*) AS n FROM favorites")[0]["n"] == 0


def test_concurrent_likes_and_playlist_insertions(catalog_db, api_client, music):
    user, headers, _, _, tracks = music
    playlist = result(
        api_client.post("/api/v1/playlists", headers=headers, json={"name": "Mix"}), 201
    )

    async def run():
        factory = async_sessionmaker(catalog_db.engine, expire_on_commit=False)

        async def like():
            async with factory() as session:
                actor = User(id=user["id"])
                await set_favorite(session, "track", tracks[0]["id"], actor)

        async def add(track):
            async with factory() as session:
                await change_tracks(
                    session,
                    playlist["id"],
                    User(id=user["id"]),
                    "add",
                    PlaylistTrackAdd(track_id=track["id"]),
                )

        await asyncio.wait_for(asyncio.gather(*(like() for _ in range(6))), timeout=15)
        await asyncio.wait_for(
            asyncio.gather(*(add(track) for track in tracks)), timeout=15
        )

    asyncio.run(run())
    assert catalog_db.execute("SELECT count(*) AS n FROM favorites")[0]["n"] == 1
    assert [
        item["position"]
        for item in result(
            api_client.get(
                f"/api/v1/playlists/{playlist['id']}/tracks", headers=headers
            )
        )["items"]
    ] == [0, 1, 2]
