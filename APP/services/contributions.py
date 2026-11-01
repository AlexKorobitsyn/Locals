from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from APP.core.constants import PRIVILEGED_LEVELS
from APP.models.contribution import Contribution
from APP.models.contribution_vote import ContributionVote
from APP.models.event import Event
from APP.models.genre import Genre
from APP.models.user import User
from APP.models.venue import Venue
from APP.schemas.contribution import ContributionOut
from APP.schemas.pagination import Page
from APP.services.activity import record_event
from APP.services.catalog import MODELS, related_rows
from APP.services.experience import experience_tier, lock_active_user
from APP.services.gamification import contribution_award

CONTRIBUTION_MODELS = {**MODELS, "venue": Venue, "event": Event}


def current_value(target, field):
    if field == "publication":
        return {"publication_status": target.publication_status}
    if field == "metadata":
        return {"name": target.name if hasattr(target, "name") else target.title}
    return (
        {"lyrics": target.lyrics}
        if field == "lyrics"
        else {"genre_ids": sorted(genre.id for genre in target.genres)}
    )


async def pending_count(session, user_id):
    return await session.scalar(
        select(func.count())
        .select_from(Contribution)
        .where(Contribution.user_id == user_id, Contribution.status == "pending")
    )


async def enforce_contribution_limit(session, user, settings):
    if (
        user.level not in PRIVILEGED_LEVELS
        and await pending_count(session, user.id)
        >= settings.contribution_limits[experience_tier(user, settings)]
    ):
        raise HTTPException(
            status_code=409,
            detail="Pending contribution limit reached; wait for existing proposals to be reviewed",
        )


async def submit_publication(session, user, target, kind, settings):
    await enforce_contribution_limit(session, user, settings)
    proposal = Contribution(
        user_id=user.id,
        target_type=kind,
        target_id=target.id,
        **{kind + "_id": target.id},
        field="publication",
        before={"publication_status": "pending"},
        proposed={
            "publication_status": "published",
            "name": target.name,
            **{
                key: (
                    getattr(target, key).isoformat()
                    if hasattr(getattr(target, key), "isoformat")
                    else getattr(target, key)
                )
                for key in (
                    "description",
                    "city_id",
                    "lat",
                    "lng",
                    *(
                        ("starts_at", "stop_at", "venue_id")
                        if kind == "event"
                        else ("address", "website", "capacity")
                    ),
                )
            },
        },
    )
    session.add(proposal)
    await session.flush()
    record_event(
        session,
        user.id,
        "contribution_submitted",
        "contribution",
        proposal.id,
        public=False,
    )


async def create_contribution(session, actor, payload, settings):
    async with session.begin():
        user = await lock_active_user(session, actor.id)
        await enforce_contribution_limit(session, user, settings)
        model = CONTRIBUTION_MODELS[payload.target_type]
        target = await session.scalar(
            select(model)
            .options(selectinload(model.genres))
            .where(model.id == payload.target_id)
            .with_for_update()
        )
        if target is None:
            raise HTTPException(status_code=404, detail="Target not found")
        if target.user_id == user.id:
            raise HTTPException(
                status_code=409, detail="Use the editor for your own content"
            )
        proposed = (
            {"name": payload.name}
            if payload.field == "metadata"
            else {"lyrics": payload.lyrics}
            if payload.field == "lyrics"
            else {"genre_ids": sorted(payload.genre_ids)}
        )
        if payload.field == "genres":
            await related_rows(session, Genre, payload.genre_ids)
        before = current_value(target, payload.field)
        if before == proposed:
            raise HTTPException(status_code=409, detail="No changes proposed")
        duplicate = await session.scalar(
            select(Contribution.id).where(
                Contribution.user_id == user.id,
                Contribution.target_type == payload.target_type,
                Contribution.target_id == target.id,
                Contribution.field == payload.field,
                Contribution.status == "pending",
            )
        )
        if duplicate is not None:
            raise HTTPException(
                status_code=409,
                detail="You already have a pending proposal for this field",
            )
        proposal = Contribution(
            user_id=user.id,
            target_type=payload.target_type,
            target_id=target.id,
            **{payload.target_type + "_id": target.id},
            field=payload.field,
            before=before,
            proposed=proposed,
        )
        session.add(proposal)
        await session.flush()
        record_event(
            session,
            user.id,
            "contribution_submitted",
            "contribution",
            proposal.id,
            public=False,
        )
        output = await proposal_output(session, proposal, actor, settings, target)
    return output


async def proposal_target(session, proposal, lock=False):
    model = CONTRIBUTION_MODELS[proposal.target_type]
    query = select(model).where(model.id == proposal.target_id)
    if hasattr(model, "genres"):
        query = query.options(selectinload(model.genres))
    if lock:
        query = query.with_for_update()
    return await session.scalar(query)


async def vote_counts(session, proposal, settings):
    total, eligible = (
        await session.execute(
            select(
                func.count(),
                func.count().filter(
                    User.experience_points >= settings.experience_lyrics_points
                ),
            )
            .select_from(ContributionVote)
            .join(User)
            .where(
                ContributionVote.contribution_id == proposal.id,
                User.is_active.is_(True),
                User.id != proposal.user_id,
            )
        )
    ).one()
    return total, eligible


async def proposal_output(session, proposal, actor, settings, target=None):
    target = target if target is not None else await proposal_target(session, proposal)
    result = ContributionOut.model_validate(proposal)
    result.votes_count, result.eligible_votes_count = await vote_counts(
        session, proposal, settings
    )
    result.is_voted_by_me = (
        actor is not None
        and await session.get(ContributionVote, (proposal.id, actor.id)) is not None
    )
    result.requires_owner = target is not None and proposal.field in getattr(
        target, "owner_fields", []
    )
    result.can_review = (
        actor is not None
        and actor.id != proposal.user_id
        and target is not None
        and (target.user_id == actor.id or actor.level in PRIVILEGED_LEVELS)
    )
    result.can_approve = result.can_review and (
        not result.requires_owner or actor.id == target.user_id
    )
    return result


async def contribution_page(
    session,
    actor,
    limit,
    offset,
    moderate=False,
    status=None,
    community=False,
    target_type=None,
    target_id=None,
):
    filters = [] if moderate or community else [Contribution.user_id == actor.id]
    if status:
        filters.append(Contribution.status == status)
    if target_type:
        filters.append(Contribution.target_type == target_type)
    if target_id:
        filters.append(Contribution.target_id == target_id)
    rows = (
        await session.scalars(
            select(Contribution)
            .where(*filters)
            .order_by(Contribution.id.desc())
            .limit(limit)
            .offset(offset)
        )
    ).all()
    settings = session.info["settings"]
    return Page[ContributionOut](
        items=[await proposal_output(session, row, actor, settings) for row in rows],
        total=await session.scalar(
            select(func.count()).select_from(Contribution).where(*filters)
        ),
        limit=limit,
        offset=offset,
    )


async def locked_proposal(session, proposal_id):
    author_id = await session.scalar(
        select(Contribution.user_id).where(Contribution.id == proposal_id)
    )
    if author_id is None:
        raise HTTPException(status_code=404, detail="Contribution not found")
    # Всегда автор, затем предложение и цель - как при создании правки.
    from APP.services.ratings import lock_user

    await lock_user(session, author_id)
    proposal = await session.scalar(
        select(Contribution).where(Contribution.id == proposal_id).with_for_update()
    )
    if proposal is None:
        raise HTTPException(status_code=404, detail="Contribution not found")
    return proposal


async def apply_proposal(session, proposal, target, settings, reviewer_id=None):
    if current_value(target, proposal.field) != proposal.before:
        raise HTTPException(
            status_code=409,
            detail="Content changed since submission; submit a fresh proposal",
        )
    if proposal.field == "publication":
        if proposal.target_type == "event" and target.venue_id is not None:
            venue = await session.get(Venue, target.venue_id)
            if venue.publication_status != "published":
                raise HTTPException(
                    status_code=409, detail="Publish the venue before its event"
                )
        target.publication_status = "published"
    elif proposal.field == "lyrics":
        target.lyrics = proposal.proposed["lyrics"]
    elif proposal.field == "metadata":
        setattr(
            target,
            "name" if hasattr(target, "name") else "title",
            proposal.proposed["name"],
        )
    else:
        target.genres = await related_rows(
            session, Genre, proposal.proposed["genre_ids"]
        )
    proposal.status, proposal.reviewer_id = "approved", reviewer_id
    if reviewer_id == target.user_id and hasattr(target, "owner_fields"):
        target.owner_fields = sorted(set(target.owner_fields) | {proposal.field})
    await contribution_award(session, proposal, settings)
    record_event(
        session,
        reviewer_id or proposal.user_id,
        proposal.target_type + "_updated",
        proposal.target_type,
        proposal.target_id,
    )
    record_event(
        session,
        reviewer_id or proposal.user_id,
        "contribution_approved",
        "contribution",
        proposal.id,
        public=False,
        payload={"community": reviewer_id is None},
    )
    await session.flush()
    await session.refresh(proposal)


async def review_contribution(session, actor, proposal_id, payload, settings):
    async with session.begin():
        proposal = await locked_proposal(session, proposal_id)
        if proposal.status != "pending":
            raise HTTPException(status_code=409, detail="Contribution already reviewed")
        target = await proposal_target(session, proposal, lock=True)
        if target is None:
            raise HTTPException(status_code=404, detail="Target not found")
        if proposal.user_id == actor.id or (
            actor.level not in PRIVILEGED_LEVELS and target.user_id != actor.id
        ):
            raise HTTPException(
                status_code=403,
                detail="Only the owner or moderator may review another user's proposal",
            )
        proposal.reason = payload.reason
        if payload.decision == "approve":
            if (
                proposal.field in getattr(target, "owner_fields", [])
                and target.user_id != actor.id
            ):
                raise HTTPException(
                    status_code=403,
                    detail="This field contains the owner's authoritative version; owner approval required",
                )
            await apply_proposal(session, proposal, target, settings, actor.id)
        else:
            proposal.status, proposal.reviewer_id = "rejected", actor.id
            if proposal.field == "publication":
                target.publication_status = "rejected"
            record_event(
                session,
                actor.id,
                "contribution_rejected",
                "contribution",
                proposal.id,
                public=False,
            )
            await session.flush()
            await session.refresh(proposal)
        output = await proposal_output(session, proposal, actor, settings, target)
    return output


async def set_vote(session, actor, proposal_id, settings, remove=False):
    async with session.begin():
        proposal = await locked_proposal(session, proposal_id)
        if proposal.status != "pending":
            raise HTTPException(status_code=409, detail="Voting is closed")
        if proposal.user_id == actor.id:
            raise HTTPException(
                status_code=403, detail="Cannot vote for your own proposal"
            )
        vote = await session.get(ContributionVote, (proposal.id, actor.id))
        if remove and vote is not None:
            await session.delete(vote)
        elif not remove and vote is None:
            session.add(ContributionVote(contribution_id=proposal.id, user_id=actor.id))
        await session.flush()
        _, eligible = await vote_counts(session, proposal, settings)
        target = await proposal_target(session, proposal, lock=True)
        if (
            target is not None
            and eligible >= settings.contribution_votes_required
            and proposal.field not in getattr(target, "owner_fields", [])
            and current_value(target, proposal.field) == proposal.before
        ):
            venue = (
                await session.get(Venue, target.venue_id)
                if isinstance(target, Event) and target.venue_id
                else None
            )
            if venue is None or venue.publication_status == "published":
                await apply_proposal(session, proposal, target, settings)
        output = await proposal_output(session, proposal, actor, settings, target)
    return output


async def withdraw_contribution(session, actor, proposal_id):
    from sqlalchemy import delete
    from sqlalchemy.exc import IntegrityError

    try:
        async with session.begin():
            proposal = await locked_proposal(session, proposal_id)
            if proposal.user_id != actor.id:
                raise HTTPException(
                    status_code=403, detail="Only the author may withdraw a proposal"
                )
            if proposal.status == "approved":
                raise HTTPException(
                    status_code=409,
                    detail="Published contributions cannot be withdrawn",
                )
            if proposal.field == "publication":
                target = await proposal_target(session, proposal, lock=True)
                if target is not None and target.publication_status != "published":
                    await session.execute(
                        delete(CONTRIBUTION_MODELS[proposal.target_type]).where(
                            CONTRIBUTION_MODELS[proposal.target_type].id
                            == proposal.target_id
                        )
                    )
            else:
                await session.delete(proposal)
            record_event(
                session,
                actor.id,
                "contribution_withdrawn",
                "contribution",
                proposal_id,
                public=False,
            )
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Remove dependent events before withdrawing the venue",
        ) from None
