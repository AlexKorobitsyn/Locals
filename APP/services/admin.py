from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from APP.core.constants import PRIVILEGED_LEVELS, UserLevel
from APP.models.auth_session import AuthSession
from APP.models.city import City
from APP.models.genre import Genre
from APP.models.user import User
from APP.schemas.admin import AdminUserOut
from APP.schemas.city import CityOut
from APP.schemas.genre import GenreOut
from APP.schemas.pagination import Page
from APP.services.activity import record_event


def admin_user_output(user, settings):
    from APP.services.experience import experience_output

    output = AdminUserOut.model_validate(user)
    experience = experience_output(user, settings)
    output.experience_level, output.level_name = (
        experience.experience_level,
        experience.level_name,
    )
    return output


async def user_page(session, limit, offset, q=None):
    filters = []
    if q:
        pattern = (
            "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        )
        filters.append(
            or_(
                User.email.ilike(pattern, escape="\\"),
                User.display_name.ilike(pattern, escape="\\"),
            )
        )
    rows = (
        await session.scalars(
            select(User)
            .options(selectinload(User.city))
            .where(*filters)
            .order_by(User.id)
            .limit(limit)
            .offset(offset)
        )
    ).all()
    total = await session.scalar(select(func.count()).select_from(User).where(*filters))
    return Page[AdminUserOut](
        items=[admin_user_output(row, session.info["settings"]) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


async def user_detail(session, user_id):
    user = await session.scalar(
        select(User)
        .options(selectinload(User.city))
        .where(User.id == user_id)
        .execution_options(populate_existing=True)
    )
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return admin_user_output(user, session.info["settings"])


async def locked_users(session, actor, target_id, moderate=False):
    # Одинаковый порядок блокировок исключает взаимную блокировку администраторов.
    rows = (
        await session.scalars(
            select(User)
            .where(User.id.in_({actor.id, target_id}))
            .order_by(User.id)
            .with_for_update(key_share=True)
            .execution_options(populate_existing=True)
        )
    ).all()
    users = {row.id: row for row in rows}
    current = users.get(actor.id)
    if (
        current is None
        or not current.is_active
        or current.level not in (PRIVILEGED_LEVELS if moderate else {UserLevel.admin})
    ):
        raise HTTPException(status_code=403, detail="Admin access required")
    if target_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    return users[target_id]


async def change_user(session, actor, target_id, payload, operation, settings=None):
    try:
        async with session.begin():
            target = await locked_users(
                session, actor, target_id, operation == "moderation_profile"
            )
            values = payload.model_dump(exclude_unset=True)
            from APP.services.experience import sync_experience_level, thresholds

            if operation == "experience":
                tier = values.pop("tier")
                values["scene_verified"] = tier >= 3
                values["experience_points"] = (
                    thresholds(settings)[tier - 1] if tier else 0
                )
            if operation in ("level", "status") and target.level == UserLevel.admin:
                raise HTTPException(
                    status_code=409,
                    detail="Admin privileges and status are managed only by the developer command",
                )
            if (
                operation in ("profile", "moderation_profile")
                and "city_id" in values
                and values["city_id"] is not None
            ):
                if await session.get(City, values["city_id"]) is None:
                    raise HTTPException(status_code=404, detail="City not found")
            changes = {}
            for key, value in values.items():
                if key == "avatar_url" and value is not None:
                    value = str(value)
                previous = getattr(target, key)
                if previous != value:
                    changes[key] = {"before": previous, "after": value}
                    setattr(target, key, UserLevel(value) if key == "level" else value)
                    if key == "avatar_url":
                        target.image_media_id = None
            if changes:
                if operation == "experience":
                    sync_experience_level(target, settings)
                if operation == "level":
                    if target.level == UserLevel.green:
                        target.experience_points = 0
                        target.scene_verified = False
                    elif (
                        target.level == UserLevel.experienced
                        and target.experience_points < settings.experience_lyrics_points
                    ):
                        target.experience_points = settings.experience_lyrics_points
                if operation in ("level", "status", "experience", "scene_verification"):
                    await session.execute(
                        update(AuthSession)
                        .where(
                            AuthSession.user_id == target.id,
                            AuthSession.revoked_at.is_(None),
                        )
                        .values(revoked_at=datetime.now(UTC))
                    )
                record_event(
                    session,
                    actor.id,
                    "admin_user_" + operation + "_updated",
                    "user",
                    target.id,
                    public=False,
                    payload={"changes": changes},
                )
                await session.flush()
            output = await user_detail(session, target.id)
        return output
    except IntegrityError as exc:
        if getattr(exc.orig, "sqlstate", None) == "23505":
            raise HTTPException(
                status_code=409, detail="Email already registered"
            ) from None
        raise


async def change_reference(session, actor, kind, entity_id, payload=None):
    model, schema = (Genre, GenreOut) if kind == "genre" else (City, CityOut)
    try:
        async with session.begin():
            entity = await session.scalar(
                select(model).where(model.id == entity_id).with_for_update()
            )
            if entity is None:
                raise HTTPException(status_code=404, detail="Reference not found")
            if payload is None:
                # Удаление справочника снимает связи по правилам внешних ключей.
                await session.execute(delete(model).where(model.id == entity_id))
                output = None
            else:
                for key, value in payload.model_dump().items():
                    setattr(entity, key, value)
                await session.flush()
                output = schema.model_validate(entity)
            record_event(
                session,
                actor.id,
                kind + ("_deleted" if payload is None else "_updated"),
                kind,
                entity_id,
            )
        return output
    except IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail="Reference is in use or duplicates an existing entry",
        ) from exc
