from typing import Literal

from fastapi import APIRouter, HTTPException, Response, UploadFile
from sqlalchemy import select
from starlette.concurrency import run_in_threadpool
from starlette.responses import RedirectResponse

from APP.core.config import SettingsDependency
from APP.core.db import SessionDependency
from APP.core.dependencies import CurrentUserDependency, OptionalUserDependency
from APP.core.storage import StorageDependency
from APP.models.media import Media
from APP.schemas.media import MediaAttach, MediaOut, PlaybackOut
from APP.schemas.pagination import EntityId
from APP.services.media import accessible_media, attach_media, playback, upload_media

router = APIRouter(tags=["media"])


@router.post("/media/images", response_model=MediaOut, status_code=201)
async def image_upload(
    file: UploadFile,
    session: SessionDependency,
    user: CurrentUserDependency,
    storage: StorageDependency,
    settings: SettingsDependency,
):
    return await upload_media(session, user, file, "image", storage, settings)


@router.post("/media/audio", response_model=MediaOut, status_code=201)
async def audio_upload(
    file: UploadFile,
    session: SessionDependency,
    user: CurrentUserDependency,
    storage: StorageDependency,
    settings: SettingsDependency,
):
    return await upload_media(session, user, file, "audio", storage, settings)


@router.get("/media/{media_id}", response_model=MediaOut)
async def metadata(
    media_id: EntityId, session: SessionDependency, user: CurrentUserDependency
):
    media = await session.scalar(
        select(Media).where(
            Media.id == media_id, Media.user_id == user.id, Media.status == "ready"
        )
    )
    if media is None:
        raise HTTPException(status_code=404, detail="Media not found")
    return MediaOut.model_validate(media)


@router.get("/media/{media_id}/content")
async def content(
    media_id: EntityId,
    session: SessionDependency,
    user: OptionalUserDependency,
    storage: StorageDependency,
):
    media = await accessible_media(session, media_id, user)
    url = await run_in_threadpool(storage.url, media.object_key, media.content_type)
    return RedirectResponse(url, status_code=307, headers={"Cache-Control": "no-store"})


@router.put("/images/{target_type}/{target_id}", status_code=204)
async def image_attach(
    target_type: Literal["user", "artist", "album", "track", "venue", "playlist"],
    target_id: EntityId,
    payload: MediaAttach,
    session: SessionDependency,
    user: CurrentUserDependency,
):
    await attach_media(session, user, payload.media_id, target_type, target_id)


@router.put("/tracks/{track_id}/audio", status_code=204)
async def audio_attach(
    track_id: EntityId,
    payload: MediaAttach,
    session: SessionDependency,
    user: CurrentUserDependency,
):
    await attach_media(session, user, payload.media_id, "track", track_id, audio=True)


@router.get("/tracks/{track_id}/playback", response_model=PlaybackOut)
async def track_playback(
    track_id: EntityId,
    session: SessionDependency,
    storage: StorageDependency,
    settings: SettingsDependency,
    response: Response,
):
    response.headers["Cache-Control"] = "no-store"
    return await playback(session, track_id, storage, settings)


@router.get("/tracks/{track_id}/audio")
async def track_audio(
    track_id: EntityId,
    session: SessionDependency,
    storage: StorageDependency,
    settings: SettingsDependency,
):
    output = await playback(session, track_id, storage, settings)
    return RedirectResponse(
        output.url, status_code=307, headers={"Cache-Control": "no-store"}
    )
