from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from APP.core.constants import DEFAULT_PAGE_LIMIT, RatingTarget
from APP.core.db import SessionDependency
from APP.core.dependencies import CurrentUserDependency, OptionalUserDependency
from APP.schemas.pagination import EntityId, Page, PageLimit, PageOffset
from APP.schemas.review import ReviewCreate, ReviewOut, ReviewUpdate
from APP.services.reviews import change_review, create_review, get_review, list_reviews

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
async def create(
    payload: ReviewCreate, session: SessionDependency, user: CurrentUserDependency
):
    return await create_review(session, payload, user)


@router.get("", response_model=Page[ReviewOut], openapi_extra={"security": [{}]})
async def listing(
    session: SessionDependency,
    viewer: OptionalUserDependency,
    response: Response,
    limit: PageLimit = DEFAULT_PAGE_LIMIT,
    offset: PageOffset = 0,
    target_type: RatingTarget | None = None,
    target_id: Annotated[int | None, Query(gt=0)] = None,
):
    response.headers["Cache-Control"] = "no-store"
    return await list_reviews(session, viewer, limit, offset, target_type, target_id)


@router.get("/{review_id}", response_model=ReviewOut, openapi_extra={"security": [{}]})
async def detail(
    review_id: EntityId,
    session: SessionDependency,
    viewer: OptionalUserDependency,
    response: Response,
):
    response.headers["Cache-Control"] = "no-store"
    return await get_review(session, review_id, viewer)


@router.patch("/{review_id}", response_model=ReviewOut)
async def update(
    review_id: EntityId,
    payload: ReviewUpdate,
    session: SessionDependency,
    user: CurrentUserDependency,
):
    return await change_review(session, review_id, user, payload)


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    review_id: EntityId, session: SessionDependency, user: CurrentUserDependency
):
    await change_review(session, review_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
