import hashlib
import logging
import math
import tempfile
import warnings
from decimal import Decimal
from pathlib import PurePath
from uuid import uuid4

from fastapi import HTTPException
from mutagen import MutagenError
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.wave import WAVE
from PIL import Image, UnidentifiedImageError
from sqlalchemy import exists, or_, select
from starlette.concurrency import run_in_threadpool

from APP.core.constants import NAME_MAX_LENGTH, UPLOAD_CHUNK_BYTES
from APP.core.dependencies import require_owner_or_admin, require_owner_or_privileged
from APP.core.metrics import PLAYBACK_LINK_REQUESTS
from APP.models.album import Album
from APP.models.artist import Artist
from APP.models.media import Media
from APP.models.playlist import Playlist
from APP.models.track import Track
from APP.models.user import User
from APP.models.venue import Venue
from APP.schemas.media import MediaOut, PlaybackOut
from APP.services.activity import record_event
from APP.services.ratings import lock_user

logger = logging.getLogger(__name__)
IMAGE_FORMATS = {
    "JPEG": ("image/jpeg", "jpg"),
    "PNG": ("image/png", "png"),
    "WEBP": ("image/webp", "webp"),
}
AUDIO_FORMATS = {
    "mp3": (MP3, "audio/mpeg"),
    "flac": (FLAC, "audio/flac"),
    "wav": (WAVE, "audio/wav"),
}
IMAGE_TARGETS = {
    "user": User,
    "artist": Artist,
    "album": Album,
    "track": Track,
    "venue": Venue,
    "playlist": Playlist,
}


def inspect_file(file, kind, filename, settings):
    file.seek(0)
    if kind == "image":
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(file) as image:
                    if (
                        image.format not in IMAGE_FORMATS
                        or getattr(image, "n_frames", 1) != 1
                    ):
                        raise HTTPException(
                            status_code=415,
                            detail="Only static JPEG, PNG and WebP are supported",
                        )
                    if image.width * image.height > settings.image_max_pixels:
                        raise HTTPException(
                            status_code=413, detail="Image dimensions exceed the limit"
                        )
                    content_type, suffix = IMAGE_FORMATS[image.format]
                    width, height = image.size
                    image.verify()
                file.seek(0)
                with Image.open(file) as image:
                    image.load()
            return content_type, suffix, dict(width=width, height=height, duration=None)
        except (
            UnidentifiedImageError,
            OSError,
            SyntaxError,
            ValueError,
            Image.DecompressionBombError,
            Image.DecompressionBombWarning,
        ):
            raise HTTPException(
                status_code=415, detail="Invalid image content"
            ) from None
    suffix = PurePath(filename).suffix.lower().removeprefix(".")
    if suffix not in AUDIO_FORMATS:
        raise HTTPException(
            status_code=415, detail="Only MP3, FLAC and WAV are supported"
        )
    parser, content_type = AUDIO_FORMATS[suffix]
    try:
        audio = parser(file)
        duration = audio.info.length
        if not math.isfinite(duration) or duration <= 0:
            raise ValueError("empty audio")
        return (
            content_type,
            suffix,
            dict(
                duration=Decimal(str(duration)).quantize(Decimal("0.000001")),
                width=None,
                height=None,
            ),
        )
    except (MutagenError, OSError, ValueError, EOFError):
        raise HTTPException(status_code=415, detail="Invalid audio content") from None


async def upload_media(session, user, upload, kind, storage, settings):
    maximum = settings.image_max_bytes if kind == "image" else settings.audio_max_bytes
    filename = (
        PurePath((upload.filename or "upload").replace("\\", "/")).name[
            :NAME_MAX_LENGTH
        ]
        or "upload"
    )
    digest, size = hashlib.sha256(), 0
    # Временный файл существует только во время обработки запроса.
    with tempfile.TemporaryFile() as file:
        while chunk := await upload.read(UPLOAD_CHUNK_BYTES):
            size += len(chunk)
            if size > maximum:
                raise HTTPException(
                    status_code=413, detail="File exceeds the upload limit"
                )
            digest.update(chunk)
            await run_in_threadpool(file.write, chunk)
        if size == 0:
            raise HTTPException(status_code=422, detail="File is empty")
        content_type, suffix, metadata = await run_in_threadpool(
            inspect_file, file, kind, filename, settings
        )
        key = f"{user.id}/{kind}/{uuid4().hex}.{suffix}"
        async with session.begin():
            await lock_user(session, user.id)
            media = Media(
                user_id=user.id,
                kind=kind,
                object_key=key,
                filename=filename,
                content_type=content_type,
                size=size,
                sha256=digest.hexdigest(),
                status="pending",
                **metadata,
            )
            session.add(media)
            await session.flush()
            record_event(
                session,
                user.id,
                "media_upload_started",
                "media",
                media.id,
                public=False,
            )
            media_id = media.id
        try:
            file.seek(0)
            await run_in_threadpool(storage.put, key, file, content_type)
            async with session.begin():
                await lock_user(session, user.id)
                media = await session.scalar(
                    select(Media).where(Media.id == media_id).with_for_update()
                )
                media.status = "ready"
                record_event(
                    session, user.id, "media_uploaded", "media", media.id, public=False
                )
                await session.flush()
                output = MediaOut.model_validate(media)
        except Exception:
            # Pending-запись сохраняет ключ при сбое между PostgreSQL и S3.
            try:
                await run_in_threadpool(storage.delete, key)
                async with session.begin():
                    await lock_user(session, user.id)
                    media = await session.get(Media, media_id)
                    if media is not None:
                        await session.delete(media)
                    record_event(
                        session,
                        user.id,
                        "media_upload_failed",
                        "media",
                        media_id,
                        public=False,
                    )
            except Exception:
                logger.error("Media cleanup deferred", extra={"media_id": media_id})
            logger.error("Media upload failed", extra={"media_id": media_id})
            raise HTTPException(
                status_code=503, detail="Upload could not be completed"
            ) from None
    return output


async def attach_media(session, user, media_id, kind, target_id, audio=False):
    model = Track if audio else IMAGE_TARGETS[kind]
    async with session.begin():
        await lock_user(session, user.id)
        target = await session.scalar(
            select(model).where(model.id == target_id).with_for_update()
        )
        if target is None:
            raise HTTPException(status_code=404, detail="Target not found")
        if model is Playlist and target.visibility == "private":
            require_owner_or_admin(target.id if model is User else target.user_id, user)
        else:
            require_owner_or_privileged(
                target.id if model is User else target.user_id, user
            )
        if model is Playlist and target.kind == "liked":
            raise HTTPException(
                status_code=409, detail="System playlist cannot be edited"
            )
        media = await session.scalar(
            select(Media)
            .where(
                Media.id == media_id, Media.user_id == user.id, Media.status == "ready"
            )
            .with_for_update(read=True, key_share=True)
        )
        if media is None:
            raise HTTPException(status_code=404, detail="Media not found")
        if media.kind != ("audio" if audio else "image"):
            raise HTTPException(
                status_code=422, detail="Media type does not match the target"
            )
        if audio:
            target.audio_media_id, target.audio_key = media.id, media.object_key
            target.duration = math.ceil(media.duration)
        else:
            target.image_media_id = media.id
            setattr(
                target,
                {User: "avatar_url", Artist: "image_url"}.get(model, "cover_url"),
                f"/api/v1/media/{media.id}/content",
            )
        public = model is not Playlist or target.visibility == "public"
        record_event(
            session,
            user.id,
            "audio_attached" if audio else "image_attached",
            kind,
            target.id,
            public=public,
        )


async def accessible_media(session, media_id, user):
    public = []
    for model in IMAGE_TARGETS.values():
        conditions = [model.image_media_id == Media.id]
        if model is Playlist:
            conditions.extend(
                [Playlist.visibility == "public", Playlist.kind == "custom"]
            )
        if model is User:
            conditions.append(User.is_active.is_(True))
        public.append(exists(select(model.id).where(*conditions).correlate(Media)))
    public.append(
        exists(
            select(Track.id).where(Track.audio_media_id == Media.id).correlate(Media)
        )
    )
    if user is not None:
        public.append(Media.user_id == user.id)
    media = await session.scalar(
        select(Media).where(Media.id == media_id, Media.status == "ready", or_(*public))
    )
    if media is None:
        raise HTTPException(status_code=404, detail="Media not found")
    return media


async def delete_media(session, user, media_id, storage):
    async with session.begin():
        await lock_user(session, user.id)
        media = await session.scalar(
            select(Media).where(Media.id == media_id, Media.user_id == user.id).with_for_update()
        )
        if media is None:
            raise HTTPException(status_code=404, detail="Media not found")
        references = [(model, model.image_media_id) for model in IMAGE_TARGETS.values()]
        references.append((Track, Track.audio_media_id))
        for model, column in references:
            if await session.scalar(select(model.id).where(column == media_id).limit(1)) is not None:
                raise HTTPException(status_code=409, detail="Media is attached")
        await run_in_threadpool(storage.delete, media.object_key)
        record_event(session, user.id, "media_deleted", "media", media.id, public=False)
        await session.delete(media)


async def playback(session, track_id, storage, settings):
    try:
        media = await session.scalar(
            select(Media)
            .join(Track, Track.audio_media_id == Media.id)
            .where(Track.id == track_id, Media.kind == "audio", Media.status == "ready")
        )
        if media is None:
            raise HTTPException(status_code=404, detail="Track audio not found")
        url = await run_in_threadpool(storage.url, media.object_key, media.content_type)
        result = PlaybackOut(
            url=url,
            expires_in=settings.s3_presign_ttl_seconds,
            content_type=media.content_type,
            duration=media.duration,
        )
    except HTTPException as exc:
        outcome = "rejected" if exc.status_code//100 == 4 else "error"
        PLAYBACK_LINK_REQUESTS.labels(outcome=outcome).inc()
        raise
    except Exception:
        PLAYBACK_LINK_REQUESTS.labels(outcome="error").inc()
        raise
    else:
        PLAYBACK_LINK_REQUESTS.labels(outcome="success").inc()
        return result
