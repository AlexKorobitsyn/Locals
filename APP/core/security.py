import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from uuid import UUID, uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from APP.core.config import Settings
from APP.core.constants import REFRESH_TOKEN_BYTES


@lru_cache
def password_context(rounds: int) -> CryptContext:
    # bcrypt_sha256 исключает усечение длинных UTF-8 паролей на границе 72 байт.
    return CryptContext(schemes=["bcrypt_sha256"], bcrypt_sha256__rounds=rounds)


def hash_password(password: str, rounds: int) -> str:
    return password_context(rounds).hash(password)


def verify_password(password: str, password_hash: str, rounds: int) -> bool:
    return password_context(rounds).verify(password, password_hash)


@lru_cache
def dummy_password_hash(rounds: int) -> str:
    return hash_password(secrets.token_urlsafe(REFRESH_TOKEN_BYTES), rounds)


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(REFRESH_TOKEN_BYTES)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(
    user_id: int,
    session_id: UUID,
    expires_at: datetime,
    settings: Settings,
    *,
    now: datetime | None = None,
) -> str:
    now = datetime.now(UTC) if now is None else now
    return jwt.encode(
        {
            "sub": str(user_id),
            "sid": str(session_id),
            "jti": str(uuid4()),
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
            "token_type": "access",
        },
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


@dataclass(frozen=True)
class AccessClaims:
    user_id: int
    session_id: UUID


def decode_access_token(token: str, settings: Settings) -> AccessClaims:
    claims = jwt.decode(
        token,
        settings.jwt_secret_key.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        options={
            "require_exp": True,
            "require_iat": True,
            "require_sub": True,
            "require_jti": True,
            "require_iss": True,
            "require_aud": True,
        },
    )
    try:
        now_seconds = int(datetime.now(UTC).timestamp())
        user_id = int(claims["sub"])
        if (
            user_id <= 0
            or str(user_id) != claims["sub"]
            or claims.get("token_type") != "access"
            or type(claims["iat"]) is not int
            or type(claims["exp"]) is not int
            or claims["iat"] > now_seconds
            or claims["exp"] <= now_seconds
            or claims["exp"] <= claims["iat"]
        ):
            raise ValueError("invalid claims")
        UUID(claims["jti"])
        return AccessClaims(user_id=user_id, session_id=UUID(claims["sid"]))
    except (KeyError, TypeError, ValueError, AttributeError):
        raise JWTError("Invalid access token claims") from None
