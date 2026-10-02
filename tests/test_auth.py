import json
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

import APP.main as main
import APP.services.auth as auth_service
from APP.core.dependencies import (
    AdminUserDependency,
    CurrentUserDependency,
    PrivilegedUserDependency,
    require_owner,
)
from APP.core.security import (
    create_access_token,
    decode_access_token,
    hash_refresh_token,
)

pytestmark = pytest.mark.integration
CREDENTIALS = {"email": "listener@example.com", "password": "long-listener-password"}


@pytest.fixture
def client(catalog_db, monkeypatch):
    monkeypatch.setattr(main, "create_engine", lambda _: catalog_db.engine)
    app = main.create_app(catalog_db.settings)

    @app.get("/api/v1/test-privileged")
    async def privileged(user: PrivilegedUserDependency):
        return {"id": user.id}

    @app.get("/api/v1/test-admin")
    async def admin(user: AdminUserDependency):
        return {"id": user.id}

    @app.get("/api/v1/test-owner/{owner_id}")
    async def owner(owner_id: int, user: CurrentUserDependency):
        require_owner(owner_id, user)
        return {"id": user.id}

    with TestClient(app) as http:
        yield http


def register(client, **changes):
    response = client.post(
        "/api/v1/auth/register",
        json=CREDENTIALS | {"display_name": "Listener"} | changes,
    )
    assert response.status_code == 201, response.text
    return response.json()


def login(client):
    response = client.post("/api/v1/auth/login", json=CREDENTIALS)
    assert response.status_code == 200, response.text
    assert response.headers["Cache-Control"] == "no-store"
    return response.json()


def bearer(tokens):
    return {"Authorization": "Bearer " + tokens["access_token"]}


def test_registration_login_private_and_public_profiles(client, catalog_db):
    registered = register(
        client, email="LISTENER@EXAMPLE.COM", display_name="  Listener  "
    )
    assert registered["email"] == CREDENTIALS["email"]
    assert registered["display_name"] == "Listener"
    assert registered["level"] == "green"
    assert registered["type"] == "user"
    assert "password_hash" not in registered
    password_hash = catalog_db.execute("SELECT password_hash FROM users")[0][
        "password_hash"
    ]
    assert password_hash != CREDENTIALS["password"]
    assert password_hash.startswith("$bcrypt-sha256$")

    tokens = login(client)
    assert tokens["expires_in"] == 15 * 60
    me = client.get("/api/v1/me", headers=bearer(tokens))
    assert me.status_code == 200
    assert me.json() == registered
    public = client.get(f"/api/v1/users/{registered['id']}")
    assert public.status_code == 200
    assert "email" not in public.json()
    assert "level" not in public.json()
    assert "password_hash" not in public.json()
    assert client.get("/api/v1/me").status_code == 401
    assert client.get("/api/v1/users/999999").status_code == 404
    assert client.get("/api/v1/users/0").status_code == 422


def test_type_is_independent_of_permissions(client, catalog_db):
    registered = register(client)
    tokens = login(client)
    catalog_db.execute(
        "INSERT INTO artists (name, user_id) VALUES ('Solo', :id)",
        {"id": registered["id"]},
    )
    assert client.get("/api/v1/me", headers=bearer(tokens)).json()["type"] == "artist"
    catalog_db.execute("UPDATE users SET level='moderator'")
    me = client.get("/api/v1/me", headers=bearer(tokens)).json()
    assert me["type"] == "artist"
    assert me["level"] == "moderator"


def test_refresh_rotation_and_immediate_logout_revocation(client, catalog_db):
    register(client)
    tokens = login(client)
    stored = catalog_db.execute(
        "SELECT refresh_token_hash, expires_at FROM auth_sessions"
    )[0]
    assert stored["refresh_token_hash"] == hash_refresh_token(tokens["refresh_token"])
    assert stored["refresh_token_hash"] != tokens["refresh_token"]
    response = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    renewed = response.json()
    assert renewed["refresh_token"] != tokens["refresh_token"]
    assert renewed["access_token"] != tokens["access_token"]
    assert (
        catalog_db.execute("SELECT expires_at FROM auth_sessions")[0]["expires_at"]
        == stored["expires_at"]
    )
    assert (
        client.post(
            "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        ).status_code
        == 401
    )
    assert (
        client.post("/api/v1/auth/logout", headers=bearer(renewed)).status_code == 204
    )
    assert client.get("/api/v1/me", headers=bearer(tokens)).status_code == 401
    assert client.get("/api/v1/me", headers=bearer(renewed)).status_code == 401
    assert (
        client.post(
            "/api/v1/auth/refresh", json={"refresh_token": renewed["refresh_token"]}
        ).status_code
        == 401
    )


def test_auth_events_are_private_and_contain_no_credentials(client, catalog_db):
    register(client)
    tokens = login(client)
    response = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert response.status_code == 200
    renewed = response.json()
    assert (
        client.post("/api/v1/auth/logout", headers=bearer(renewed)).status_code == 204
    )
    rows = catalog_db.execute(
        "SELECT action, payload, is_public FROM event_logs ORDER BY id"
    )
    assert [row["action"] for row in rows] == [
        "playlist_created",
        "user_registered",
        "user_logged_in",
        "session_refreshed",
        "user_logged_out",
    ]
    assert all(not row["is_public"] for row in rows)
    serialized = json.dumps([dict(row) for row in rows])
    for secret in [
        CREDENTIALS["password"],
        tokens["access_token"],
        tokens["refresh_token"],
        renewed["refresh_token"],
    ]:
        assert secret not in serialized


def test_audit_failure_rolls_back_registration(client, catalog_db, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("event log unavailable")

    monkeypatch.setattr(auth_service, "record_auth_event", fail)
    with pytest.raises(RuntimeError, match="event log unavailable"):
        client.post(
            "/api/v1/auth/register", json=CREDENTIALS | {"display_name": "Listener"}
        )
    assert catalog_db.execute("SELECT count(*) AS count FROM users")[0]["count"] == 0
    assert (
        catalog_db.execute("SELECT count(*) AS count FROM event_logs")[0]["count"] == 0
    )


def test_audit_failure_rolls_back_refresh(client, catalog_db, monkeypatch):
    register(client)
    tokens = login(client)
    original = auth_service.record_auth_event

    def fail(*args, **kwargs):
        raise RuntimeError("event log unavailable")

    monkeypatch.setattr(auth_service, "record_auth_event", fail)
    with pytest.raises(RuntimeError, match="event log unavailable"):
        client.post(
            "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        )
    stored = catalog_db.execute("SELECT refresh_token_hash FROM auth_sessions")[0][
        "refresh_token_hash"
    ]
    assert stored == hash_refresh_token(tokens["refresh_token"])
    monkeypatch.setattr(auth_service, "record_auth_event", original)
    assert (
        client.post(
            "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        ).status_code
        == 200
    )


def test_logout_only_revokes_current_device(client):
    register(client)
    first = login(client)
    second = login(client)
    assert client.post("/api/v1/auth/logout", headers=bearer(first)).status_code == 204
    assert client.get("/api/v1/me", headers=bearer(first)).status_code == 401
    assert client.get("/api/v1/me", headers=bearer(second)).status_code == 200


def test_auth_sessions_survive_application_restart(catalog_db, monkeypatch):
    monkeypatch.setattr(main, "create_engine", lambda _: catalog_db.engine)
    with TestClient(main.create_app(catalog_db.settings)) as first:
        register(first)
        tokens = login(first)
    with TestClient(main.create_app(catalog_db.settings)) as restarted:
        assert restarted.get("/api/v1/me", headers=bearer(tokens)).status_code == 200
        assert (
            restarted.post("/api/v1/auth/logout", headers=bearer(tokens)).status_code
            == 204
        )
    with TestClient(main.create_app(catalog_db.settings)) as restarted_again:
        assert (
            restarted_again.get("/api/v1/me", headers=bearer(tokens)).status_code == 401
        )


def test_concurrent_refresh_only_succeeds_once(client):
    register(client)
    tokens = login(client)

    def refresh(_):
        return client.post(
            "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        )

    with ThreadPoolExecutor(max_workers=2) as workers:
        responses = list(workers.map(refresh, range(2)))
    assert sorted(response.status_code for response in responses) == [200, 401]
    valid = next(
        response.json() for response in responses if response.status_code == 200
    )
    assert client.get("/api/v1/me", headers=bearer(valid)).status_code == 200


def test_concurrent_registration_is_unique(client, catalog_db):
    payload = CREDENTIALS | {"display_name": "Listener"}
    with ThreadPoolExecutor(max_workers=2) as workers:
        statuses = list(
            workers.map(
                lambda _: (
                    client.post("/api/v1/auth/register", json=payload).status_code
                ),
                range(2),
            )
        )
    assert sorted(statuses) == [201, 409]
    assert catalog_db.execute("SELECT count(*) AS count FROM users")[0]["count"] == 1


def test_permissions_use_current_database_level(client, catalog_db):
    user = register(client)
    tokens = login(client)
    headers = bearer(tokens)
    assert client.get("/api/v1/test-privileged", headers=headers).status_code == 403
    assert (
        client.get(f"/api/v1/test-owner/{user['id']}", headers=headers).status_code
        == 200
    )
    assert (
        client.get(f"/api/v1/test-owner/{user['id'] + 1}", headers=headers).status_code
        == 403
    )
    for level in ("experienced", "moderator", "admin"):
        catalog_db.execute("UPDATE users SET level=:level", {"level": level})
        assert client.get("/api/v1/test-privileged", headers=headers).status_code == (
            403 if level == "experienced" else 200
        )
        expected = 200 if level == "admin" else 403
        assert client.get("/api/v1/test-admin", headers=headers).status_code == expected
    catalog_db.execute("UPDATE users SET level='green'")
    assert client.get("/api/v1/test-admin", headers=headers).status_code == 403


def test_deactivated_user_cannot_login_refresh_or_use_access(client, catalog_db):
    user = register(client)
    tokens = login(client)
    catalog_db.execute("UPDATE users SET is_active=false")
    assert client.get("/api/v1/me", headers=bearer(tokens)).status_code == 401
    assert client.post("/api/v1/auth/login", json=CREDENTIALS).status_code == 401
    assert (
        client.post(
            "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        ).status_code
        == 401
    )
    assert client.get(f"/api/v1/users/{user['id']}").status_code == 404


def test_expired_access_can_be_renewed_but_expired_session_cannot(client, catalog_db):
    user = register(client)
    tokens = login(client)
    claims = decode_access_token(tokens["access_token"], catalog_db.settings)
    now = datetime.now(UTC)
    expired = create_access_token(
        user["id"],
        claims.session_id,
        now - timedelta(minutes=1),
        catalog_db.settings,
        now=now - timedelta(minutes=2),
    )
    assert (
        client.get(
            "/api/v1/me", headers={"Authorization": "Bearer " + expired}
        ).status_code
        == 401
    )
    renewed = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert renewed.status_code == 200
    catalog_db.execute(
        "UPDATE auth_sessions SET created_at=now()-interval '2 days', expires_at=now()-interval '1 day'"
    )
    assert client.get("/api/v1/me", headers=bearer(renewed.json())).status_code == 401
    assert (
        client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": renewed.json()["refresh_token"]},
        ).status_code
        == 401
    )


@pytest.mark.parametrize("header", ["Bearer invalid", "Basic abc", "Bearer"])
def test_invalid_optional_credentials_are_not_ignored(client, header):
    user = register(client)
    response = client.get(
        f"/api/v1/users/{user['id']}", headers={"Authorization": header}
    )
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_signup_cannot_escalate_privileges_and_login_errors_are_uniform(client):
    for forbidden in ("level", "weight", "is_active", "type"):
        response = client.post(
            "/api/v1/auth/register",
            json=CREDENTIALS | {"display_name": "Listener", forbidden: "admin"},
        )
        assert response.status_code == 422
    register(client)
    unknown = client.post(
        "/api/v1/auth/login", json=CREDENTIALS | {"email": "unknown@example.com"}
    )
    wrong = client.post(
        "/api/v1/auth/login", json=CREDENTIALS | {"password": "incorrect-password"}
    )
    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json() == wrong.json()


def test_access_token_for_wrong_session_user_is_rejected(client, catalog_db):
    user = register(client)
    tokens = login(client)
    claims = decode_access_token(tokens["access_token"], catalog_db.settings)
    token = create_access_token(
        user["id"] + 1,
        claims.session_id,
        datetime.now(UTC) + timedelta(minutes=1),
        catalog_db.settings,
    )
    assert (
        client.get(
            "/api/v1/me", headers={"Authorization": "Bearer " + token}
        ).status_code
        == 401
    )
