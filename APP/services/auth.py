from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.concurrency import run_in_threadpool

from APP.core.config import Settings
from APP.core.dependencies import unauthorized
from APP.core.security import (
    create_access_token,
    dummy_password_hash,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from APP.models.auth_session import AuthSession
from APP.models.event_log import EventLog
from APP.models.user import User
from APP.schemas.auth import LoginInput, RegisterInput, TokenPair
from APP.services.library import ensure_liked

UNIQUE_VIOLATION = "23505"


def record_auth_event(
    session: AsyncSession, action: str, user_id: int, session_id: UUID | None = None
) -> None:
    session.add(
        EventLog(
            actor_id=user_id,
            action=action,
            target_type="user",
            target_id=user_id,
            payload={"session_id": str(session_id)} if session_id is not None else {},
            is_public=False,
        )
    )


async def register_user(
    session: AsyncSession, payload: RegisterInput, settings: Settings
) -> User:
    password_hash = await run_in_threadpool(
        hash_password, payload.password.get_secret_value(), settings.bcrypt_rounds
    )
    try:
        async with session.begin():
            user = User(
                email=str(payload.email),
                password_hash=password_hash,
                display_name=payload.display_name,
            )
            session.add(user)
            await session.flush()
            await ensure_liked(session, user.id)
            user = await session.scalar(
                select(User).options(selectinload(User.city)).where(User.id == user.id)
            )
            record_auth_event(session, "user_registered", user.id)
        return user
    except IntegrityError as exc:
        if getattr(exc.orig, "sqlstate", None) == UNIQUE_VIOLATION:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
            ) from None
        raise


def token_pair(
    user_id: int,
    auth_session: AuthSession,
    refresh_token: str,
    settings: Settings,
    now: datetime,
) -> TokenPair:
    expires_at = min(
        now + timedelta(minutes=settings.access_token_ttl_minutes),
        auth_session.expires_at,
    )
    expires_in = int((expires_at - now).total_seconds())
    refresh_expires_in = int((auth_session.expires_at - now).total_seconds())
    if expires_in <= 0 or refresh_expires_in <= 0:
        raise unauthorized()
    return TokenPair(
        access_token=create_access_token(
            user_id, auth_session.id, expires_at, settings, now=now
        ),
        refresh_token=refresh_token,
        expires_in=expires_in,
        refresh_expires_in=refresh_expires_in,
    )


async def login_user(
    session: AsyncSession, payload: LoginInput, settings: Settings
) -> TokenPair:
    async with session.begin():
        user = await session.scalar(
            select(User).where(func.lower(User.email) == str(payload.email))
        )
        password_hash = (
            user.password_hash
            if user is not None
            else await run_in_threadpool(dummy_password_hash, settings.bcrypt_rounds)
        )
        valid = await run_in_threadpool(
            verify_password,
            payload.password.get_secret_value(),
            password_hash,
            settings.bcrypt_rounds,
        )
        if not valid or user is None or not user.is_active:
            raise unauthorized()
        now = datetime.now(UTC)
        refresh_token = generate_refresh_token()
        auth_session = AuthSession(
            id=uuid4(),
            user_id=user.id,
            refresh_token_hash=hash_refresh_token(refresh_token),
            expires_at=now + timedelta(days=settings.refresh_token_ttl_days),
        )
        session.add(auth_session)
        await session.flush()
        pair = token_pair(user.id, auth_session, refresh_token, settings, now)
        record_auth_event(session, "user_logged_in", user.id, auth_session.id)
    return pair


async def refresh_session(
    session: AsyncSession, refresh_token: str, settings: Settings
) -> TokenPair:
    async with session.begin():
        result = await session.execute(
            select(AuthSession, User)
            .join(User, User.id == AuthSession.user_id)
            .where(AuthSession.refresh_token_hash == hash_refresh_token(refresh_token))
            .with_for_update(of=AuthSession)
        )
        row = result.one_or_none()
        now = datetime.now(UTC)
        if (
            row is None
            or row.AuthSession.revoked_at is not None
            or row.AuthSession.expires_at <= now
            or not row.User.is_active
        ):
            raise unauthorized()
        new_refresh_token = generate_refresh_token()
        row.AuthSession.refresh_token_hash = hash_refresh_token(new_refresh_token)
        await session.flush()
        pair = token_pair(
            row.User.id, row.AuthSession, new_refresh_token, settings, now
        )
        record_auth_event(session, "session_refreshed", row.User.id, row.AuthSession.id)
    return pair


async def logout_session(session: AsyncSession, session_id: UUID) -> None:
    async with session.begin():
        user_id = await session.scalar(
            update(AuthSession)
            .where(AuthSession.id == session_id, AuthSession.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
            .returning(AuthSession.user_id)
        )
        if user_id is not None:
            record_auth_event(session, "user_logged_out", user_id, session_id)


async def logout_refresh_session(session: AsyncSession, refresh_token: str) -> None:
    async with session.begin():
        row = (
            await session.execute(
                select(AuthSession)
                .where(
                    AuthSession.refresh_token_hash == hash_refresh_token(refresh_token)
                )
                .with_for_update()
            )
        ).scalar_one_or_none()
        if row is not None and row.revoked_at is None:
            row.revoked_at = datetime.now(UTC)
            record_auth_event(session, "user_logged_out", row.user_id, row.id)
