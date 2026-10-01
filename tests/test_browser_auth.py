import pytest
from fastapi.testclient import TestClient

from APP import main
from APP.core.browser_auth import REFRESH_COOKIE_NAME, REFRESH_COOKIE_PATH
from APP.core.security import hash_refresh_token

pytestmark = pytest.mark.integration
ORIGIN = "https://locals.test"
HEADERS = {"Origin": ORIGIN, "X-CSRF-Protection": "1"}
CREDENTIALS = {"email": "browser@example.com", "password": "browser-test-password"}


@pytest.fixture
def browser_client(catalog_db, monkeypatch):
    catalog_db.settings.browser_allowed_origins = [ORIGIN]
    monkeypatch.setattr(main, "create_engine", lambda _: catalog_db.engine)
    with TestClient(main.create_app(catalog_db.settings), base_url=ORIGIN) as client:
        registered = client.post(
            "/api/v1/auth/register",
            json={**CREDENTIALS, "display_name": "Browser listener"},
        )
        assert registered.status_code == 201
        yield client


def login(client):
    response = client.post(
        "/api/v1/auth/browser/login", json=CREDENTIALS, headers=HEADERS
    )
    assert response.status_code == 200, response.text
    return response


def bearer(response):
    return {"Authorization": "Bearer " + response.json()["access_token"]}


def test_browser_refresh_rotation_cookie_flags_and_logout(browser_client, catalog_db):
    response = login(browser_client)
    cookie = response.headers["set-cookie"]
    assert "HttpOnly" in cookie and "Secure" in cookie and "SameSite=lax" in cookie
    assert f"Path={REFRESH_COOKIE_PATH}" in cookie
    assert "refresh_token" not in response.json()
    assert response.headers["cache-control"] == "no-store"
    old_token = browser_client.cookies.get(REFRESH_COOKIE_NAME)
    stored = catalog_db.execute("SELECT refresh_token_hash FROM auth_sessions")[0]
    assert stored["refresh_token_hash"] == hash_refresh_token(old_token)
    renewed = browser_client.post("/api/v1/auth/browser/refresh", headers=HEADERS)
    assert renewed.status_code == 200
    assert renewed.json()["session_id"] == response.json()["session_id"]
    assert browser_client.cookies.get(REFRESH_COOKIE_NAME) != old_token
    replay = browser_client.post(
        "/api/v1/auth/refresh", json={"refresh_token": old_token}
    )
    assert replay.status_code == 401
    assert browser_client.get("/api/v1/me", headers=bearer(renewed)).status_code == 200
    logout = browser_client.post("/api/v1/auth/browser/logout", headers=HEADERS)
    assert logout.status_code == 204
    assert browser_client.cookies.get(REFRESH_COOKIE_NAME) is None
    assert browser_client.get("/api/v1/me", headers=bearer(renewed)).status_code == 401
    assert browser_client.get("/api/v1/me", headers=bearer(response)).status_code == 401
    assert (
        browser_client.post("/api/v1/auth/browser/logout", headers=HEADERS).status_code
        == 204
    )


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Origin": ORIGIN},
        {"X-CSRF-Protection": "1"},
        {**HEADERS, "Origin": "https://attacker.test"},
        {**HEADERS, "Origin": "null"},
        {**HEADERS, "Sec-Fetch-Site": "cross-site"},
    ],
)
def test_browser_csrf_rejects_login_refresh_and_logout(
    browser_client, catalog_db, headers
):
    login(browser_client)
    current_cookie = browser_client.cookies.get(REFRESH_COOKIE_NAME)
    for endpoint in ("login", "refresh", "logout"):
        response = browser_client.post(
            f"/api/v1/auth/browser/{endpoint}",
            json=CREDENTIALS if endpoint == "login" else None,
            headers=headers,
        )
        assert response.status_code == 403
    stored = catalog_db.execute(
        "SELECT refresh_token_hash, revoked_at FROM auth_sessions"
    )
    assert len(stored) == 1
    assert stored[0]["refresh_token_hash"] == hash_refresh_token(current_cookie)
    assert stored[0]["revoked_at"] is None


def test_browser_revoked_cookie_is_cleared_and_json_api_is_unchanged(browser_client):
    browser = login(browser_client)
    assert (
        browser_client.post("/api/v1/auth/logout", headers=bearer(browser)).status_code
        == 204
    )
    refreshed = browser_client.post("/api/v1/auth/browser/refresh", headers=HEADERS)
    assert refreshed.status_code == 401
    assert browser_client.cookies.get(REFRESH_COOKIE_NAME) is None
    json_login = browser_client.post("/api/v1/auth/login", json=CREDENTIALS)
    assert json_login.status_code == 200
    assert "refresh_token" in json_login.json()
    assert "set-cookie" not in json_login.headers
    assert (
        browser_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": json_login.json()["refresh_token"]},
        ).status_code
        == 200
    )
