from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi import HTTPException
from jose import JWTError, jwt

from APP.core.constants import UserLevel
from APP.core.dependencies import require_owner, require_owner_or_privileged
from APP.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from APP.models.user import User


def test_long_unicode_password_is_not_truncated():
    password = "пароль" * 15
    encoded = hash_password(password, rounds=4)
    assert verify_password(password, encoded, rounds=4)
    assert not verify_password(password[:-1] + "!", encoded, rounds=4)


def test_access_claims_round_trip(settings):
    session_id = uuid4()
    token = create_access_token(
        1, session_id, datetime.now(UTC) + timedelta(minutes=1), settings
    )
    claims = decode_access_token(token, settings)
    assert claims.user_id == 1
    assert claims.session_id == session_id


def test_access_expires_at_exact_exp_boundary(settings):
    now = datetime.now(UTC)
    token = create_access_token(
        1, uuid4(), now, settings, now=now - timedelta(minutes=1)
    )
    with pytest.raises(JWTError):
        decode_access_token(token, settings)


@pytest.mark.parametrize(
    "change",
    [
        {"aud": "other-service"},
        {"iss": "other-service"},
        {"token_type": "refresh"},
        {"sid": "invalid"},
        {"sub": "0"},
        {"sub": "-1"},
        {"sub": "01"},
        {"iat": True},
        {"iat": int((datetime.now(UTC) + timedelta(days=1)).timestamp())},
    ],
)
def test_invalid_claims_rejected(settings, change):
    token = create_access_token(
        1, uuid4(), datetime.now(UTC) + timedelta(days=2), settings
    )
    payload = jwt.get_unverified_claims(token) | change
    tampered = jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(JWTError):
        decode_access_token(tampered, settings)


@pytest.mark.parametrize("missing", ["exp", "iat", "sid", "sub", "jti", "iss", "aud"])
def test_missing_claim_rejected(settings, missing):
    token = create_access_token(
        1, uuid4(), datetime.now(UTC) + timedelta(minutes=1), settings
    )
    payload = jwt.get_unverified_claims(token)
    payload.pop(missing)
    token = jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(JWTError):
        decode_access_token(token, settings)


def test_wrong_key_and_algorithm_rejected(settings):
    token = create_access_token(
        1, uuid4(), datetime.now(UTC) + timedelta(minutes=1), settings
    )
    payload = jwt.get_unverified_claims(token)
    for key, algorithm in [
        ("wrong-secret-key", "HS256"),
        (settings.jwt_secret_key.get_secret_value(), "HS384"),
    ]:
        forged = jwt.encode(payload, key, algorithm=algorithm)
        with pytest.raises(JWTError):
            decode_access_token(forged, settings)


def test_owner_does_not_implicitly_grant_admin_access():
    user = User(id=1, level=UserLevel.green)
    require_owner(1, user)
    with pytest.raises(HTTPException) as error:
        require_owner(None, user)
    assert error.value.status_code == 403
    with pytest.raises(HTTPException):
        require_owner_or_privileged(2, user)
    user.level = UserLevel.admin
    require_owner_or_privileged(2, user)
    with pytest.raises(HTTPException):
        require_owner(2, user)
