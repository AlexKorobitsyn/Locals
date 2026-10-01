from fastapi import APIRouter, Response, status

from APP.core.constants import DEFAULT_PAGE_LIMIT, FollowTarget
from APP.core.db import SessionDependency
from APP.core.dependencies import CurrentUserDependency
from APP.schemas.follow import FollowCreate, FollowOut
from APP.schemas.pagination import EntityId, Page, PageLimit, PageOffset
from APP.services.social import following_page, set_follow

router = APIRouter(tags=["follows"])


@router.put("/follows", response_model=FollowOut)
async def put(
    payload: FollowCreate, session: SessionDependency, user: CurrentUserDependency
):
    return await set_follow(session, user, payload.target_type.value, payload.target_id)


@router.delete(
    "/follows/{target_type}/{target_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove(
    target_type: FollowTarget,
    target_id: EntityId,
    session: SessionDependency,
    user: CurrentUserDependency,
):
    await set_follow(session, user, target_type.value, target_id, remove=True)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me/following", response_model=Page[FollowOut])
async def listing(
    session: SessionDependency,
    user: CurrentUserDependency,
    response: Response,
    limit: PageLimit = DEFAULT_PAGE_LIMIT,
    offset: PageOffset = 0,
):
    response.headers["Cache-Control"] = "no-store"
    return await following_page(session, user, limit, offset)
