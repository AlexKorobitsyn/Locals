from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from APP.core.constants import PRIVILEGED_LEVELS, UserLevel
from APP.core.security import decode_access_token
from APP.models.auth_session import AuthSession
from APP.models.user import User

bearer = HTTPBearer(auto_error=False, scheme_name="BearerAuth")
BearerCredentials = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]


def unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


@dataclass(frozen=True)
class AuthIdentity:
    user: User
    session_id: UUID


async def get_optional_auth(
    request: Request, credentials: BearerCredentials
) -> AuthIdentity | None:
    if credentials is None:
        if request.headers.get("Authorization") is not None:
            raise unauthorized()
        return None
    try:
        claims = decode_access_token(
            credentials.credentials, request.app.state.settings
        )
    except JWTError:
        raise unauthorized() from None
    # Отдельная read-сессия не начинает транзакцию будущей операции сервиса.
    async with request.app.state.session_factory() as session:
        result = await session.execute(
            select(AuthSession, User)
            .join(User, User.id == AuthSession.user_id)
            .options(selectinload(User.city))
            .where(
                AuthSession.id == claims.session_id,
                AuthSession.user_id == claims.user_id,
                AuthSession.revoked_at.is_(None),
                AuthSession.expires_at > datetime.now(UTC),
                User.is_active.is_(True),
            )
        )
        row = result.one_or_none()
        if row is None:
            raise unauthorized()
        return AuthIdentity(user=row.User, session_id=row.AuthSession.id)


OptionalAuthDependency = Annotated[AuthIdentity | None, Depends(get_optional_auth)]


async def get_current_auth(identity: OptionalAuthDependency) -> AuthIdentity:
    if identity is None:
        raise unauthorized()
    return identity


CurrentAuthDependency = Annotated[AuthIdentity, Depends(get_current_auth)]


async def get_current_user(identity: CurrentAuthDependency) -> User:
    return identity.user


async def get_optional_user(identity: OptionalAuthDependency) -> User | None:
    return identity.user if identity is not None else None


CurrentUserDependency = Annotated[User, Depends(get_current_user)]
OptionalUserDependency = Annotated[User | None, Depends(get_optional_user)]


def require_levels(*levels: UserLevel):
    allowed = frozenset(levels)

    async def check(user: CurrentUserDependency) -> User:
        if user.level not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return user

    return check


PrivilegedUserDependency = Annotated[User, Depends(require_levels(*PRIVILEGED_LEVELS))]
AdminUserDependency = Annotated[User, Depends(require_levels(UserLevel.admin))]


def require_owner(owner_id: int | None, user: User) -> None:
    if owner_id is None or owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Owner access required"
        )


def require_owner_or_privileged(owner_id: int | None, user: User) -> None:
    if user.level not in PRIVILEGED_LEVELS:
        require_owner(owner_id, user)


def require_owner_or_admin(owner_id: int | None, user: User) -> None:
    if user.level != UserLevel.admin:
        require_owner(owner_id, user)
