from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response
from sqlalchemy import delete, func, select
from sqlalchemy.orm import selectinload

from APP.core.config import SettingsDependency
from APP.core.constants import DEFAULT_PAGE_LIMIT, NAME_MAX_LENGTH
from APP.core.db import SessionDependency
from APP.core.dependencies import AdminUserDependency, PrivilegedUserDependency
from APP.models.event import Event
from APP.models.event_log import EventLog
from APP.models.playlist import Playlist
from APP.models.user import User
from APP.models.venue import Venue
from APP.schemas.admin import (
    AdminUserOut,
    AdminUserUpdate,
    ModeratedProfileUpdate,
    SceneVerificationPut,
    UserLevelPut,
    UserStatusPut,
)
from APP.schemas.city import CityCreate, CityOut
from APP.schemas.common import BaseSchema
from APP.schemas.experience import (
    CommunityAwardCreate,
    ExperienceOut,
    ExperienceTierPut,
)
from APP.schemas.genre import GenreCreate, GenreOut
from APP.schemas.pagination import EntityId, Page, PageLimit, PageOffset
from APP.schemas.playlist import PlaylistShort
from APP.schemas.user import UserOut
from APP.services.activity import record_event
from APP.services.admin import (
    admin_user_output,
    change_reference,
    change_user,
    user_detail,
    user_page,
)
from APP.services.library import playlist_output, playlist_query

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/profiles", response_model=Page[UserOut])
async def profiles(
    session: SessionDependency,
    actor: PrivilegedUserDependency,
    response: Response,
    limit: PageLimit = DEFAULT_PAGE_LIMIT,
    offset: PageOffset = 0,
):
    response.headers["Cache-Control"] = "no-store"
    rows = (
        await session.scalars(
            select(User)
            .options(selectinload(User.city))
            .where(User.is_active.is_(True))
            .order_by(User.id)
            .limit(limit)
            .offset(offset)
        )
    ).all()
    return Page[UserOut](
        items=[
            UserOut.model_validate(admin_user_output(row, session.info["settings"]))
            for row in rows
        ],
        total=await session.scalar(
            select(func.count()).select_from(User).where(User.is_active.is_(True))
        ),
        limit=limit,
        offset=offset,
    )


@router.patch("/profiles/{user_id}", response_model=UserOut)
async def change_profile(
    user_id: EntityId,
    payload: ModeratedProfileUpdate,
    session: SessionDependency,
    actor: PrivilegedUserDependency,
    response: Response,
):
    response.headers["Cache-Control"] = "no-store"
    result = await change_user(session, actor, user_id, payload, "moderation_profile")
    return UserOut.model_validate(result)


@router.get("/users", response_model=Page[AdminUserOut])
async def users(
    session: SessionDependency,
    actor: AdminUserDependency,
    response: Response,
    limit: PageLimit = DEFAULT_PAGE_LIMIT,
    offset: PageOffset = 0,
    q: Annotated[str | None, Query(max_length=NAME_MAX_LENGTH)] = None,
):
    response.headers["Cache-Control"] = "no-store"
    return await user_page(session, limit, offset, q)


@router.get("/users/{user_id}", response_model=AdminUserOut)
async def detail(
    user_id: EntityId,
    session: SessionDependency,
    actor: AdminUserDependency,
    response: Response,
):
    response.headers["Cache-Control"] = "no-store"
    return await user_detail(session, user_id)


@router.patch("/users/{user_id}", response_model=AdminUserOut)
async def profile(
    user_id: EntityId,
    payload: AdminUserUpdate,
    session: SessionDependency,
    actor: AdminUserDependency,
    response: Response,
):
    response.headers["Cache-Control"] = "no-store"
    return await change_user(session, actor, user_id, payload, "profile")


@router.put("/users/{user_id}/level", response_model=AdminUserOut)
async def level(
    user_id: EntityId,
    payload: UserLevelPut,
    session: SessionDependency,
    actor: AdminUserDependency,
    response: Response,
    settings: SettingsDependency,
):
    response.headers["Cache-Control"] = "no-store"
    return await change_user(session, actor, user_id, payload, "level", settings)


@router.put("/users/{user_id}/status", response_model=AdminUserOut)
async def status(
    user_id: EntityId,
    payload: UserStatusPut,
    session: SessionDependency,
    actor: AdminUserDependency,
    response: Response,
):
    response.headers["Cache-Control"] = "no-store"
    return await change_user(session, actor, user_id, payload, "status")


@router.put("/genres/{genre_id}", response_model=GenreOut)
async def genre(
    genre_id: EntityId,
    payload: GenreCreate,
    session: SessionDependency,
    actor: PrivilegedUserDependency,
):
    return await change_reference(session, actor, "genre", genre_id, payload)


@router.delete("/genres/{genre_id}", status_code=204)
async def remove_genre(
    genre_id: EntityId, session: SessionDependency, actor: PrivilegedUserDependency
):
    await change_reference(session, actor, "genre", genre_id)


@router.put("/cities/{city_id}", response_model=CityOut)
async def city(
    city_id: EntityId,
    payload: CityCreate,
    session: SessionDependency,
    actor: PrivilegedUserDependency,
):
    return await change_reference(session, actor, "city", city_id, payload)


@router.delete("/cities/{city_id}", status_code=204)
async def remove_city(
    city_id: EntityId, session: SessionDependency, actor: PrivilegedUserDependency
):
    await change_reference(session, actor, "city", city_id)


class AuditOut(BaseSchema):
    id: int
    actor_id: int | None
    action: str
    target_type: str
    target_id: int
    payload: dict
    created_at: datetime


@router.get("/audit", response_model=Page[AuditOut])
async def audit(
    session: SessionDependency,
    actor: AdminUserDependency,
    response: Response,
    limit: PageLimit = DEFAULT_PAGE_LIMIT,
    offset: PageOffset = 0,
):
    response.headers["Cache-Control"] = "no-store"
    rows = (
        await session.scalars(
            select(EventLog).order_by(EventLog.id.desc()).limit(limit).offset(offset)
        )
    ).all()
    return Page[AuditOut](
        items=[AuditOut.model_validate(row) for row in rows],
        total=await session.scalar(select(func.count()).select_from(EventLog)),
        limit=limit,
        offset=offset,
    )


@router.get("/playlists", response_model=Page[PlaylistShort])
async def playlists(
    session: SessionDependency,
    actor: AdminUserDependency,
    response: Response,
    limit: PageLimit = DEFAULT_PAGE_LIMIT,
    offset: PageOffset = 0,
):
    response.headers["Cache-Control"] = "no-store"
    rows = (
        await session.execute(
            playlist_query(actor).order_by(Playlist.id).limit(limit).offset(offset)
        )
    ).all()
    return Page[PlaylistShort](
        items=[playlist_output(row, actor, details=False) for row in rows],
        total=await session.scalar(select(func.count()).select_from(Playlist)),
        limit=limit,
        offset=offset,
    )


@router.delete("/venues/{venue_id}", status_code=204)
async def remove_venue(
    venue_id: EntityId, session: SessionDependency, actor: PrivilegedUserDependency
):
    async with session.begin():
        venue = await session.scalar(
            select(Venue).where(Venue.id == venue_id).with_for_update()
        )
        if venue is None:
            raise HTTPException(status_code=404, detail="Venue not found")
        if await session.scalar(
            select(Event.id).where(Event.venue_id == venue_id).limit(1)
        ):
            raise HTTPException(
                status_code=409,
                detail="Move or delete the venue's events before deleting it",
            )
        record_event(session, actor.id, "venue_deleted", "venue", venue_id)
        await session.execute(delete(Venue).where(Venue.id == venue_id))


@router.put("/users/{user_id}/experience", response_model=AdminUserOut)
async def experience(
    user_id: EntityId,
    payload: ExperienceTierPut,
    session: SessionDependency,
    actor: AdminUserDependency,
    response: Response,
    settings: SettingsDependency,
):
    response.headers["Cache-Control"] = "no-store"
    return await change_user(session, actor, user_id, payload, "experience", settings)


@router.post("/users/{user_id}/community-awards", response_model=ExperienceOut)
async def select_winner(
    user_id: EntityId,
    payload: CommunityAwardCreate,
    actor: AdminUserDependency,
    session: SessionDependency,
    settings: SettingsDependency,
):
    from APP.services.gamification import community_award

    return await community_award(session, actor, user_id, payload, settings)


@router.put("/users/{user_id}/scene-verification", response_model=AdminUserOut)
async def verify_scene(
    user_id: EntityId,
    payload: SceneVerificationPut,
    actor: AdminUserDependency,
    session: SessionDependency,
):
    return await change_user(session, actor, user_id, payload, "scene_verification")
