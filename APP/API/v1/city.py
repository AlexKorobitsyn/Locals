from fastapi import APIRouter

from APP.core.constants import DEFAULT_PAGE_LIMIT
from APP.core.db import SessionDependency
from APP.core.dependencies import PrivilegedUserDependency
from APP.schemas.city import CityCreate, CityOut
from APP.schemas.pagination import EntityId, Page, PageLimit, PageOffset
from APP.services.places import city_detail, city_page, create_city

router = APIRouter(prefix="/cities", tags=["cities"])


@router.get("", response_model=Page[CityOut])
async def cities(
    session: SessionDependency,
    limit: PageLimit = DEFAULT_PAGE_LIMIT,
    offset: PageOffset = 0,
    q: str | None = None,
):
    return await city_page(session, limit, offset, q)


@router.get("/{city_id}", response_model=CityOut)
async def detail(city_id: EntityId, session: SessionDependency):
    return await city_detail(session, city_id)


@router.post("", response_model=CityOut, status_code=201)
async def create(
    payload: CityCreate, session: SessionDependency, user: PrivilegedUserDependency
):
    return await create_city(session, payload, user)
