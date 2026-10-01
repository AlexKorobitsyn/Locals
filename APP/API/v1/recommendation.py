from fastapi import APIRouter, Response

from APP.core.config import SettingsDependency
from APP.core.constants import DEFAULT_PAGE_LIMIT
from APP.core.db import SessionDependency
from APP.core.dependencies import OptionalUserDependency
from APP.schemas.pagination import PageLimit, PageOffset
from APP.schemas.recommendation import RecommendationPage
from APP.services.recommendations import recommend_tracks

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get(
    "/tracks", response_model=RecommendationPage, openapi_extra={"security": [{}]}
)
async def tracks(
    session: SessionDependency,
    user: OptionalUserDependency,
    settings: SettingsDependency,
    response: Response,
    limit: PageLimit = DEFAULT_PAGE_LIMIT,
    offset: PageOffset = 0,
    playable_only: bool = False,
):
    response.headers["Cache-Control"] = "no-store"
    return await recommend_tracks(session, user, settings, limit, offset, playable_only)
