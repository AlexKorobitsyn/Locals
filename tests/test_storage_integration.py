import hashlib
import os
from urllib.request import Request, urlopen

import pytest
from pydantic import SecretStr
from test_library import music as music
from test_library import result
from test_media import image_bytes, wav_bytes

from APP.core.storage import ObjectStorage

pytestmark = pytest.mark.integration


def test_real_s3_upload_playback_range_and_private_bucket(api_client, music):
    endpoint = os.environ.get("TEST_S3_ENDPOINT_URL")
    if not endpoint:
        pytest.skip(
            "Set TEST_S3_ENDPOINT_URL and credentials to check real object storage"
        )
    settings = api_client.app.state.settings.model_copy(
        update={
            "s3_endpoint_url": endpoint,
            "s3_public_endpoint_url": endpoint,
            "s3_access_key": SecretStr(os.environ["TEST_S3_ACCESS_KEY"]),
            "s3_secret_key": SecretStr(os.environ["TEST_S3_SECRET_KEY"]),
            "s3_bucket": os.environ.get("TEST_S3_BUCKET", "music"),
        }
    )
    storage = ObjectStorage(settings)
    api_client.app.state.storage = storage
    _, headers, artist, _, tracks = music
    try:
        raw = image_bytes()
        image = result(
            api_client.post(
                "/api/v1/media/images",
                headers=headers,
                files={"file": ("image.png", raw, "image/png")},
            ),
            201,
        )
        result(
            api_client.put(
                f"/api/v1/images/artist/{artist['id']}",
                headers=headers,
                json={"media_id": image["id"]},
            ),
            204,
        )
        response = api_client.get(
            f"/api/v1/media/{image['id']}/content", follow_redirects=False
        )
        with urlopen(response.headers["location"], timeout=10) as content:
            assert content.read() == raw
        raw_audio = wav_bytes()
        audio = result(
            api_client.post(
                "/api/v1/media/audio",
                headers=headers,
                files={"file": ("audio.wav", raw_audio, "audio/wav")},
            ),
            201,
        )
        result(
            api_client.put(
                f"/api/v1/tracks/{tracks[0]['id']}/audio",
                headers=headers,
                json={"media_id": audio["id"]},
            ),
            204,
        )
        playback = result(api_client.get(f"/api/v1/tracks/{tracks[0]['id']}/playback"))
        with urlopen(
            Request(playback["url"], headers={"Range": "bytes=0-43"}), timeout=10
        ) as response:
            assert response.status == 206 and response.read() == raw_audio[:44]
        with urlopen(playback["url"], timeout=10) as response:
            assert hashlib.sha256(response.read()).hexdigest() == audio["sha256"]
        assert "X-Amz-Signature" in playback["url"]
        policy = storage.client.get_bucket_acl(Bucket=settings.s3_bucket)
        assert not any(
            grant["Grantee"].get("URI", "").endswith("AllUsers")
            for grant in policy["Grants"]
        )
    finally:
        # Удаляем только объекты, созданные этим тестом в собственной схеме БД.
        import asyncio

        from sqlalchemy import select

        from APP.models.media import Media

        async def keys():
            async with api_client.app.state.session_factory() as session:
                return list((await session.scalars(select(Media.object_key))).all())

        for key in asyncio.run(keys()):
            storage.delete(key)
        storage.close()
        api_client.app.state.storage = None
