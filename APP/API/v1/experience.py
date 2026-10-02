from uuid import UUID

from fastapi import APIRouter, Response

from APP.core.config import SettingsDependency
from APP.core.constants import DEFAULT_PAGE_LIMIT
from APP.core.db import SessionDependency
from APP.core.dependencies import CurrentUserDependency
from APP.schemas.experience import (
    ExperienceAwardOut,
    ExperienceOut,
    ListeningHeartbeat,
    ListeningOut,
)
from APP.schemas.pagination import EntityId, Page, PageLimit, PageOffset
from APP.services.experience import (
    claim_quality,
    experience_output,
    heartbeat,
    start_listening,
)
from APP.services.gamification import award_history, claim_milestones

router = APIRouter(tags=["experience"])


@router.get("/me/experience", response_model=ExperienceOut)
async def progress(
    user: CurrentUserDependency, settings: SettingsDependency, response: Response
):
    response.headers["Cache-Control"] = "no-store"
    return experience_output(user, settings)


@router.post("/me/experience/claim", response_model=ExperienceOut)
async def claim(
    user: CurrentUserDependency,
    settings: SettingsDependency,
    session: SessionDependency,
    response: Response,
):
    response.headers["Cache-Control"] = "no-store"
    await claim_quality(session, user, settings)
    return await claim_milestones(session, user, settings)


@router.post(
    "/tracks/{track_id}/listening", response_model=ListeningOut, status_code=201
)
async def start(
    track_id: EntityId,
    user: CurrentUserDependency,
    settings: SettingsDependency,
    session: SessionDependency,
    response: Response,
):
    response.headers["Cache-Control"] = "no-store"
    return await start_listening(session, user, track_id, settings)


@router.put("/listening/{listening_id}", response_model=ListeningOut)
async def ping(
    listening_id: UUID,
    payload: ListeningHeartbeat,
    user: CurrentUserDependency,
    settings: SettingsDependency,
    session: SessionDependency,
    response: Response,
):
    response.headers["Cache-Control"] = "no-store"
    return await heartbeat(session, user, listening_id, payload.is_playing, settings)


@router.get("/me/experience/awards", response_model=Page[ExperienceAwardOut])
async def history(
    user: CurrentUserDependency,
    session: SessionDependency,
    response: Response,
    limit: PageLimit = DEFAULT_PAGE_LIMIT,
    offset: PageOffset = 0,
):
    response.headers["Cache-Control"] = "no-store"
    return await award_history(session, user, limit, offset)
