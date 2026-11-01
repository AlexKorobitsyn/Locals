import asyncio
import hashlib
import io
import wave

import pytest
from PIL import Image
from starlette.formparsers import MultiPartException
from test_library import music as music
from test_library import result

from APP.core.upload_limit import UploadLimitMiddleware

pytestmark = pytest.mark.integration


class MemoryStorage:
    def __init__(self):
        self.objects = {}
        self.fail = False
        self.closed = False

    def put(self, key, body, content_type):
        self.objects[key] = body.read()
        if self.fail:
            raise OSError("private internal storage error")

    def delete(self, key):
        self.objects.pop(key, None)

    def url(self, key, content_type):
        return "https://storage.example.com/music/" + key + "?signature=test"

    def close(self):
        self.closed = True


@pytest.fixture
def storage(api_client):
    instance = MemoryStorage()
    api_client.app.state.storage = instance
    return instance


def image_bytes(format="PNG"):
    file = io.BytesIO()
    Image.new("RGB", (12, 10), (100, 20, 30)).save(file, format=format)
    return file.getvalue()


def wav_bytes():
    file = io.BytesIO()
    with wave.open(file, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(8000)
        audio.writeframes(b"\0" * 16000)
    return file.getvalue()


def test_upload_actual_content_attach_permissions_and_playback(
    api_client, music, account, storage, catalog_db
):
    user, headers, artist, _, tracks = music
    _, other = account("other")
    raw = image_bytes()
    image = result(
        api_client.post(
            "/api/v1/media/images",
            headers=headers,
            files={"file": ("fake.jpg", raw, "text/plain")},
        ),
        201,
    )
    assert image["content_type"] == "image/png" and image["width"] == 12
    assert image["sha256"] == hashlib.sha256(raw).hexdigest()
    assert (
        api_client.get(
            f"/api/v1/media/{image['id']}/content", follow_redirects=False
        ).status_code
        == 404
    )
    assert (
        api_client.get(f"/api/v1/media/{image['id']}", headers=other).status_code == 404
    )
    path = f"/api/v1/images/artist/{artist['id']}"
    assert (
        api_client.put(path, headers=other, json={"media_id": image["id"]}).status_code
        == 403
    )
    result(api_client.put(path, headers=headers, json={"media_id": image["id"]}), 204)
    assert (
        result(api_client.get(f"/api/v1/artists/{artist['id']}"))["image_url"]
        == f"/api/v1/media/{image['id']}/content"
    )
    redirect = api_client.get(
        f"/api/v1/media/{image['id']}/content", follow_redirects=False
    )
    assert (
        redirect.status_code == 307 and redirect.headers["cache-control"] == "no-store"
    )
    audio = result(
        api_client.post(
            "/api/v1/media/audio",
            headers=headers,
            files={"file": ("sample.wav", wav_bytes(), "audio/wav")},
        ),
        201,
    )
    assert audio["duration"] == 1 and audio["kind"] == "audio"
    track_id = tracks[0]["id"]
    assert (
        api_client.put(
            f"/api/v1/tracks/{track_id}/audio",
            headers=headers,
            json={"media_id": image["id"]},
        ).status_code
        == 422
    )
    result(
        api_client.put(
            f"/api/v1/tracks/{track_id}/audio",
            headers=headers,
            json={"media_id": audio["id"]},
        ),
        204,
    )
    output = result(api_client.get(f"/api/v1/tracks/{track_id}/playback"))
    assert (
        output["duration"] == 1
        and output["content_type"] == "audio/wav"
        and output["expires_in"] == 300
    )
    assert (
        result(api_client.get(f"/api/v1/tracks/{track_id}"))["audio_media_id"]
        == audio["id"]
    )
    assert result(api_client.get(f"/api/v1/tracks/{track_id}"))["duration"] == 1
    assert (
        api_client.get(
            f"/api/v1/tracks/{track_id}/audio", follow_redirects=False
        ).status_code
        == 307
    )
    assert (
        catalog_db.execute("SELECT count(*) AS n FROM media WHERE status='ready'")[0][
            "n"
        ]
        == 2
    )
    assert len(storage.objects) == 2


@pytest.mark.parametrize("format", ["JPEG", "PNG", "WEBP"])
def test_supported_image_content(api_client, account, storage, format):
    _, headers = account()
    result(
        api_client.post(
            "/api/v1/media/images",
            headers=headers,
            files={"file": ("image", image_bytes(format), "application/octet-stream")},
        ),
        201,
    )


def test_private_playlist_image_visibility(api_client, account, storage):
    user, headers = account("owner")
    _, other = account("other")
    image = result(
        api_client.post(
            "/api/v1/media/images",
            headers=headers,
            files={"file": ("image.png", image_bytes(), "image/png")},
        ),
        201,
    )
    playlist = result(
        api_client.post("/api/v1/playlists", headers=headers, json={"name": "Private"}),
        201,
    )
    result(
        api_client.put(
            f"/api/v1/images/playlist/{playlist['id']}",
            headers=headers,
            json={"media_id": image["id"]},
        ),
        204,
    )
    path = f"/api/v1/media/{image['id']}/content"
    assert (
        api_client.get(path, headers=other, follow_redirects=False).status_code == 404
    )
    assert (
        api_client.get(path, headers=headers, follow_redirects=False).status_code == 307
    )
    result(
        api_client.patch(
            f"/api/v1/playlists/{playlist['id']}",
            headers=headers,
            json={"visibility": "public"},
        )
    )
    assert api_client.get(path, follow_redirects=False).status_code == 307
    result(
        api_client.patch(
            f"/api/v1/playlists/{playlist['id']}",
            headers=headers,
            json={"visibility": "private"},
        )
    )
    assert api_client.get(path, follow_redirects=False).status_code == 404


@pytest.mark.parametrize(
    "path,name,body,code",
    [
        ("images", "bad.jpg", b"<svg>bad</svg>", 415),
        ("audio", "fake.mp3", b"fake audio", 415),
        ("audio", "fake.flac", wav_bytes(), 415),
        ("audio", "file.ogg", wav_bytes(), 415),
        ("images", "empty.png", b"", 422),
    ],
)
def test_invalid_uploads_leave_no_rows(
    api_client, account, storage, catalog_db, path, name, body, code
):
    _, headers = account()
    assert (
        api_client.post(
            "/api/v1/media/" + path,
            headers=headers,
            files={"file": (name, body, "application/octet-stream")},
        ).status_code
        == code
    )
    assert storage.objects == {}
    assert catalog_db.execute("SELECT count(*) AS n FROM media")[0]["n"] == 0


def test_file_limit_dimensions_and_storage_failure(
    api_client, account, storage, catalog_db
):
    _, headers = account()
    settings = api_client.app.state.settings
    settings.image_max_bytes = 20
    assert (
        api_client.post(
            "/api/v1/media/images",
            headers=headers,
            files={"file": ("image.png", image_bytes(), "image/png")},
        ).status_code
        == 413
    )
    settings.image_max_bytes = 10000
    settings.image_max_pixels = 10
    assert (
        api_client.post(
            "/api/v1/media/images",
            headers=headers,
            files={"file": ("image.png", image_bytes(), "image/png")},
        ).status_code
        == 413
    )
    settings.image_max_pixels = 25000000
    storage.fail = True
    response = api_client.post(
        "/api/v1/media/images",
        headers=headers,
        files={"file": ("image.png", image_bytes(), "image/png")},
    )
    assert response.status_code == 503 and "private" not in response.text
    assert storage.objects == {}
    assert catalog_db.execute("SELECT count(*) AS n FROM media")[0]["n"] == 0


def test_upload_finalize_failure_compensates(
    api_client, account, storage, catalog_db, monkeypatch
):
    import APP.services.media as media

    _, headers = account()
    original = media.record_event

    def fail(session, actor_id, action, *args, **kwargs):
        if action == "media_uploaded":
            raise RuntimeError("audit unavailable")
        return original(session, actor_id, action, *args, **kwargs)

    monkeypatch.setattr(media, "record_event", fail)
    assert (
        api_client.post(
            "/api/v1/media/images",
            headers=headers,
            files={"file": ("image.png", image_bytes(), "image/png")},
        ).status_code
        == 503
    )
    assert (
        storage.objects == {}
        and catalog_db.execute("SELECT count(*) AS n FROM media")[0]["n"] == 0
    )


def test_body_limit_handles_chunked_without_content_length(settings):
    from APP.core.constants import UPLOAD_CHUNK_BYTES

    messages = []

    async def endpoint(scope, receive, send):
        try:
            while True:
                body = await receive()
                if not body.get("more_body"):
                    break
        except MultiPartException:
            await send({"type": "http.response.start", "status": 400, "headers": []})
            await send({"type": "http.response.body", "body": b"oversized"})

    async def receive():
        return {
            "type": "http.request",
            "body": b"x" * UPLOAD_CHUNK_BYTES,
            "more_body": True,
        }

    async def send(message):
        messages.append(message)

    settings.image_max_bytes = 20
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/media/images",
        "headers": [],
    }
    asyncio.run(UploadLimitMiddleware(endpoint, settings)(scope, receive, send))
    assert messages[0]["status"] == 413

def test_delete_media_owner_unattached_and_references(api_client, music, account, storage):
    _, headers, _, _, tracks = music
    _, other = account("media-delete-other")
    media = result(api_client.post("/api/v1/media/audio", headers=headers, files={"file": ("slo-probe.wav", wav_bytes(), "audio/wav")}), 201)
    path = f"/api/v1/media/{media['id']}"
    assert api_client.delete(path).status_code == 401
    assert api_client.delete(path, headers=other).status_code == 404
    assert len(storage.objects) == 1
    track_id = tracks[0]["id"]
    result(api_client.put(f"/api/v1/tracks/{track_id}/audio", headers=headers, json={"media_id": media["id"]}), 204)
    assert api_client.delete(path, headers=headers).status_code == 409
    unattached = result(api_client.post("/api/v1/media/audio", headers=headers, files={"file": ("slo-probe.wav", wav_bytes(), "audio/wav")}), 201)
    path = f"/api/v1/media/{unattached['id']}"
    assert len(storage.objects) == 2
    result(api_client.delete(path, headers=headers), 204)
    assert len(storage.objects) == 1
    assert api_client.get(path, headers=headers).status_code == 404
    assert api_client.delete(path, headers=headers).status_code == 404
    assert result(api_client.get(f"/api/v1/tracks/{track_id}"))["audio_media_id"] == media["id"]
