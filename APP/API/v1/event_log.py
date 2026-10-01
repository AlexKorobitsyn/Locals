from fastapi import APIRouter, Response

from APP.core.constants import DEFAULT_PAGE_LIMIT
from APP.core.db import SessionDependency
from APP.core.dependencies import CurrentUserDependency
from APP.schemas.event_log import ActivityOut
from APP.schemas.pagination import Page, PageLimit, PageOffset
from APP.services.social import feed_page

router = APIRouter(tags=["feed"])


@router.get("/me/feed", response_model=Page[ActivityOut])
async def feed(
    session: SessionDependency,
    user: CurrentUserDependency,
    response: Response,
    limit: PageLimit = DEFAULT_PAGE_LIMIT,
    offset: PageOffset = 0,
):
    response.headers["Cache-Control"] = "no-store"
    return await feed_page(session, user, limit, offset)
