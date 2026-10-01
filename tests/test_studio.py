import pytest

from APP.core.constants import DEFAULT_PAGE_LIMIT

pytestmark = pytest.mark.integration
KINDS = ("artists", "albums", "tracks")
PAGE_SIZE = 2
TRACK_DURATION_SECONDS = 60


def create_music(client, headers, name):
    def create(kind, payload):
        response = client.post(f"/api/v1/{kind}", headers=headers, json=payload)
        assert response.status_code == 201, response.text
        return response.json()

    artist = create("artists", {"name": name})
    album = create("albums", {"title": name, "artist_ids": [artist["id"]]})
    track = create(
        "tracks",
        {
            "title": name,
            "duration": TRACK_DURATION_SECONDS,
            "artist_ids": [artist["id"]],
            "album_id": album["id"],
        },
    )
    return {"artists": artist, "albums": album, "tracks": track}


@pytest.fixture
def publications(api_client, account):
    first_user, first_headers = account("first_author")
    second_user, second_headers = account("second_author")
    first = [create_music(api_client, first_headers, name) for name in ("C", "A", "B")]
    second = create_music(api_client, second_headers, "Other author")
    return first_user, first_headers, first, second_user, second_headers, second


@pytest.mark.parametrize("kind", KINDS)
def test_studio_ownership_pagination_sorting_and_public_catalog(
    api_client, publications, catalog_db, kind
):
    first_user, headers, own, other_user, other_headers, other = publications
    own_ids = {item[kind]["id"] for item in own}
    sort = "name" if kind == "artists" else "title"
    response = api_client.get(
        f"/api/v1/me/{kind}",
        headers=headers,
        params={"limit": PAGE_SIZE, "offset": 0, "sort": sort},
    )
    assert response.status_code == 200, response.text
    assert response.headers["Cache-Control"] == "no-store"
    page = response.json()
    assert page["total"] == len(own)
    assert page["limit"] == PAGE_SIZE and page["offset"] == 0
    assert [item[sort] for item in page["items"]] == ["A", "B"]
    assert {item["id"] for item in page["items"]} <= own_ids
    last = api_client.get(
        f"/api/v1/me/{kind}?limit={PAGE_SIZE}&offset={PAGE_SIZE}&sort={sort}",
        headers=headers,
    ).json()
    assert [item[sort] for item in last["items"]] == ["C"]
    assert last["total"] == len(own)
    beyond = api_client.get(f"/api/v1/me/{kind}?offset=100", headers=headers).json()
    assert beyond["items"] == [] and beyond["total"] == len(own)
    descending = api_client.get(
        f"/api/v1/me/{kind}?sort=-{sort}", headers=headers
    ).json()
    assert [item[sort] for item in descending["items"]] == ["C", "B", "A"]
    for level in ("green", "admin"):
        catalog_db.execute(
            "UPDATE users SET level=:level WHERE id=:id",
            {"level": level, "id": other_user["id"]},
        )
        # Владельца определяет сессия, даже если клиент передал чужой user_id.
        theirs = api_client.get(
            f"/api/v1/me/{kind}?user_id={first_user['id']}", headers=other_headers
        ).json()
        assert theirs["total"] == 1
        assert [item["id"] for item in theirs["items"]] == [other[kind]["id"]]
    public = api_client.get(f"/api/v1/{kind}").json()
    assert public["total"] == len(own) + 1
    assert {item["id"] for item in public["items"]} == own_ids | {other[kind]["id"]}


@pytest.mark.parametrize("kind", KINDS)
def test_studio_empty_auth_validation_and_revoked_session(api_client, account, kind):
    _, headers = account()
    path = f"/api/v1/me/{kind}"
    assert api_client.get(path).status_code == 401
    assert (
        api_client.get(path, headers={"Authorization": "Bearer invalid"}).status_code
        == 401
    )
    empty = api_client.get(path, headers=headers)
    assert empty.status_code == 200
    assert empty.json() == {
        "items": [],
        "total": 0,
        "limit": DEFAULT_PAGE_LIMIT,
        "offset": 0,
    }
    for query in ("limit=0", "limit=101", "offset=-1", "sort=password_hash"):
        assert api_client.get(f"{path}?{query}", headers=headers).status_code == 422
    assert api_client.post("/api/v1/auth/logout", headers=headers).status_code == 204
    assert api_client.get(path, headers=headers).status_code == 401


@pytest.mark.parametrize("kind", KINDS)
def test_studio_preserves_my_ratings_and_favorites(api_client, account, kind):
    _, headers = account()
    publication = create_music(api_client, headers, "Owned")[kind]
    target_type = kind.removesuffix("s")
    rating = api_client.put(
        "/api/v1/ratings",
        headers=headers,
        json={"target_type": target_type, "target_id": publication["id"], "value": 4.5},
    )
    assert rating.status_code == 200, rating.text
    favorite = api_client.put(
        "/api/v1/favorites",
        headers=headers,
        json={"entity_type": target_type, "entity_id": publication["id"]},
    )
    assert favorite.status_code == 200, favorite.text
    item = api_client.get(f"/api/v1/me/{kind}", headers=headers).json()["items"][0]
    assert item["my_rating"] == 4.5 and item["ratings_count"] == 1
    assert item["is_liked_by_me"] and item["likes_count"] == 1
    if kind == "albums":
        assert len(item["artists"]) == 1
