from fastapi import APIRouter, Response

from APP.core.config import SettingsDependency
from APP.core.constants import RatingTarget
from APP.core.db import SessionDependency
from APP.core.dependencies import CurrentUserDependency
from APP.schemas.pagination import EntityId
from APP.schemas.rating import RatingPut, RatingResult
from APP.services.ratings import delete_rating, put_rating

router = APIRouter(prefix="/ratings", tags=["ratings"])


@router.put("", response_model=RatingResult)
async def put(
    payload: RatingPut,
    session: SessionDependency,
    user: CurrentUserDependency,
    settings: SettingsDependency,
    response: Response,
):
    response.headers["Cache-Control"] = "no-store"
    return await put_rating(session, payload, user, settings)


@router.delete("/{target_type}/{target_id}", response_model=RatingResult)
async def delete(
    target_type: RatingTarget,
    target_id: EntityId,
    session: SessionDependency,
    user: CurrentUserDependency,
    settings: SettingsDependency,
    response: Response,
):
    response.headers["Cache-Control"] = "no-store"
    return await delete_rating(session, target_type, target_id, user, settings)
