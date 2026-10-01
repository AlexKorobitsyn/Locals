from fastapi import APIRouter, Response, status

from APP.core.constants import DEFAULT_PAGE_LIMIT, FavoriteTarget
from APP.core.db import SessionDependency
from APP.core.dependencies import CurrentUserDependency
from APP.schemas.favorite import FavoriteCreate, FavoriteRead
from APP.schemas.pagination import EntityId, Page, PageLimit, PageOffset
from APP.services.library import list_favorites, set_favorite

router = APIRouter(tags=["favorites"])


@router.put("/favorites", response_model=FavoriteRead)
@router.post(
    "/favorites", response_model=FavoriteRead, status_code=status.HTTP_201_CREATED
)
async def put(
    payload: FavoriteCreate, session: SessionDependency, user: CurrentUserDependency
):
    return await set_favorite(
        session, payload.entity_type.value, payload.entity_id, user
    )


@router.delete(
    "/favorites/{entity_type}/{entity_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove(
    entity_type: FavoriteTarget,
    entity_id: EntityId,
    session: SessionDependency,
    user: CurrentUserDependency,
):
    await set_favorite(session, entity_type.value, entity_id, user, remove=True)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me/favorites", response_model=Page[FavoriteRead])
async def listing(
    session: SessionDependency,
    user: CurrentUserDependency,
    response: Response,
    limit: PageLimit = DEFAULT_PAGE_LIMIT,
    offset: PageOffset = 0,
    entity_type: FavoriteTarget | None = None,
):
    response.headers["Cache-Control"] = "no-store"
    return await list_favorites(session, user, limit, offset, entity_type)
