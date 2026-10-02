from typing import Annotated, Literal

from fastapi import APIRouter, Query, Response

from APP.core.config import SettingsDependency
from APP.core.constants import DEFAULT_PAGE_LIMIT
from APP.core.db import SessionDependency
from APP.core.dependencies import CurrentUserDependency, PrivilegedUserDependency
from APP.schemas.contribution import (
    ContributionCreate,
    ContributionOut,
    ContributionReview,
)
from APP.schemas.pagination import EntityId, Page, PageLimit, PageOffset
from APP.services.contributions import (
    contribution_page,
    create_contribution,
    review_contribution,
    set_vote,
)

router = APIRouter(tags=["contributions"])


@router.post("/contributions", response_model=ContributionOut, status_code=201)
async def create(
    payload: ContributionCreate,
    user: CurrentUserDependency,
    session: SessionDependency,
    settings: SettingsDependency,
):
    return await create_contribution(session, user, payload, settings)


@router.get("/me/contributions", response_model=Page[ContributionOut])
async def own(
    user: CurrentUserDependency,
    session: SessionDependency,
    response: Response,
    limit: PageLimit = DEFAULT_PAGE_LIMIT,
    offset: PageOffset = 0,
):
    response.headers["Cache-Control"] = "no-store"
    return await contribution_page(session, user, limit, offset)


@router.get("/admin/contributions", response_model=Page[ContributionOut])
async def queue(
    user: PrivilegedUserDependency,
    session: SessionDependency,
    response: Response,
    limit: PageLimit = DEFAULT_PAGE_LIMIT,
    offset: PageOffset = 0,
    status: Literal["pending", "approved", "rejected"] | None = None,
):
    response.headers["Cache-Control"] = "no-store"
    return await contribution_page(
        session, user, limit, offset, moderate=True, status=status
    )


@router.put("/admin/contributions/{contribution_id}", response_model=ContributionOut)
async def review(
    contribution_id: EntityId,
    payload: ContributionReview,
    user: PrivilegedUserDependency,
    session: SessionDependency,
    settings: SettingsDependency,
):
    return await review_contribution(session, user, contribution_id, payload, settings)


@router.get("/contributions", response_model=Page[ContributionOut])
async def community(
    user: CurrentUserDependency,
    session: SessionDependency,
    response: Response,
    limit: PageLimit = DEFAULT_PAGE_LIMIT,
    offset: PageOffset = 0,
    status: Literal["pending", "approved", "rejected"] | None = "pending",
    target_type: Literal["track", "album", "artist", "venue", "event"] | None = None,
    target_id: Annotated[int | None, Query(gt=0)] = None,
):
    response.headers["Cache-Control"] = "no-store"
    return await contribution_page(
        session,
        user,
        limit,
        offset,
        community=True,
        status=status,
        target_type=target_type,
        target_id=target_id,
    )


@router.put("/contributions/{contribution_id}/vote", response_model=ContributionOut)
async def vote(
    contribution_id: EntityId,
    user: CurrentUserDependency,
    session: SessionDependency,
    settings: SettingsDependency,
):
    return await set_vote(session, user, contribution_id, settings)


@router.delete("/contributions/{contribution_id}/vote", response_model=ContributionOut)
async def unvote(
    contribution_id: EntityId,
    user: CurrentUserDependency,
    session: SessionDependency,
    settings: SettingsDependency,
):
    return await set_vote(session, user, contribution_id, settings, remove=True)


@router.put("/contributions/{contribution_id}/review", response_model=ContributionOut)
async def owner_review(
    contribution_id: EntityId,
    payload: ContributionReview,
    user: CurrentUserDependency,
    session: SessionDependency,
    settings: SettingsDependency,
):
    return await review_contribution(session, user, contribution_id, payload, settings)


@router.delete("/contributions/{contribution_id}", status_code=204)
async def withdraw(
    contribution_id: EntityId, user: CurrentUserDependency, session: SessionDependency
):
    from APP.services.contributions import withdraw_contribution

    await withdraw_contribution(session, user, contribution_id)
