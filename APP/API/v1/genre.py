from fastapi import APIRouter, status

from APP.core.constants import DEFAULT_PAGE_LIMIT
from APP.core.db import SessionDependency
from APP.core.dependencies import PrivilegedUserDependency
from APP.schemas.genre import GenreCreate, GenreOut
from APP.schemas.pagination import Page, PageLimit, PageOffset
from APP.services.catalog import create_genre, list_genres

router = APIRouter(prefix="/genres", tags=["genres"])


@router.get("", response_model=Page[GenreOut])
async def list_public_genres(
    session: SessionDependency,
    limit: PageLimit = DEFAULT_PAGE_LIMIT,
    offset: PageOffset = 0,
):
    return await list_genres(session, limit, offset)


@router.post("", response_model=GenreOut, status_code=status.HTTP_201_CREATED)
async def create(
    payload: GenreCreate, session: SessionDependency, user: PrivilegedUserDependency
):
    return await create_genre(session, payload, user)
