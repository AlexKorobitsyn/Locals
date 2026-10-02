import asyncio
import os
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

import APP.API.health as health
import APP.main as main
from APP.core.config import Settings
from APP.core.db import SessionDependency, check_database, create_engine


def test_health_when_database_is_unavailable(settings):
    with TestClient(main.create_app(settings)) as client:
        assert client.get("/api/v1/health/live").json() == {"status": "ok"}
        response = client.get("/api/v1/health/ready")
        assert response.status_code == 503
        assert response.json() == {"status": "unavailable", "database": "unavailable"}
        assert "test:test" not in response.text
        assert client.get("/api/v1/docs").status_code == 200
        assert client.get("/api/v1/openapi.json").status_code == 200


def test_ready_when_database_responds(settings, monkeypatch):
    check = AsyncMock()
    monkeypatch.setattr(health, "check_database", check)
    with TestClient(main.create_app(settings)) as client:
        response = client.get("/api/v1/health/ready")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "database": "ok"}
        check.assert_awaited_once()


@pytest.mark.parametrize(
    "error", [TimeoutError(), SQLAlchemyError("private connection data")]
)
def test_ready_failure_is_sanitized(settings, monkeypatch, error):
    monkeypatch.setattr(health, "check_database", AsyncMock(side_effect=error))
    with TestClient(main.create_app(settings)) as client:
        response = client.get("/api/v1/health/ready")
        assert response.status_code == 503
        assert "private" not in response.text


def test_engine_disposed_and_sessions_closed(settings, monkeypatch):
    engine = AsyncMock()
    monkeypatch.setattr(main, "create_engine", lambda _: engine)
    closed = []

    @asynccontextmanager
    async def session_factory():
        try:
            from types import SimpleNamespace

            yield SimpleNamespace(info={})
        finally:
            closed.append(True)

    monkeypatch.setattr(main, "create_session_factory", lambda _: session_factory)
    app = main.create_app(settings)

    @app.get("/api/v1/test-session")
    async def session_route(session: SessionDependency):
        assert session is not None
        return {"status": "ok"}

    @app.get("/api/v1/test-failed-session")
    async def failed_session_route(session: SessionDependency):
        raise RuntimeError("operation failed")

    with TestClient(app, raise_server_exceptions=False) as client:
        assert client.get("/api/v1/test-session").status_code == 200
        assert client.get("/api/v1/test-failed-session").status_code == 500
        assert len(closed) == 2
    engine.dispose.assert_awaited_once()


def test_engine_disposed_on_lifespan_error(settings, monkeypatch):
    engine = AsyncMock()
    monkeypatch.setattr(main, "create_engine", lambda _: engine)
    app = main.create_app(settings)

    async def fail():
        with pytest.raises(RuntimeError):
            async with main.lifespan(app):
                raise RuntimeError("application failed")

    asyncio.run(fail())
    engine.dispose.assert_awaited_once()


def test_readiness_is_bounded_by_timeout():
    engine = AsyncMock()

    @asynccontextmanager
    async def slow_connection():
        await asyncio.sleep(10)
        yield AsyncMock()

    engine.connect = slow_connection
    with pytest.raises(TimeoutError):
        asyncio.run(check_database(engine, timeout_seconds=0.01))


@pytest.mark.integration
def test_real_postgresql_health_and_session_cleanup(monkeypatch):
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to run PostgreSQL integration checks")
    settings = Settings(_env_file=None, database_url=url)
    app = main.create_app(settings)

    @app.get("/api/v1/test-database")
    async def database_route(session: SessionDependency):
        result = await session.execute(text("SELECT 1"))
        return {"result": result.scalar_one()}

    with TestClient(app) as client:
        assert client.get("/api/v1/health/ready").status_code == 200
        assert client.get("/api/v1/test-database").json() == {"result": 1}
        assert app.state.engine.sync_engine.pool.checkedout() == 0

    async def check_connection_released():
        engine = create_engine(settings)
        try:
            async with engine.connect() as connection:
                assert (await connection.execute(text("SELECT 1"))).scalar_one() == 1
        finally:
            await engine.dispose()

    asyncio.run(check_connection_released())


def test_release_version_matches_runtime_settings(settings):
    settings.release_id = "sha-test-release"
    with TestClient(main.create_app(settings)) as client:
        response = client.get("/api/v1/health/version")
        assert response.json() == {"release_id": "sha-test-release"}
        assert response.headers["Cache-Control"] == "no-store"


def test_cors_allows_configured_frontend_only(settings):
    from pydantic import AnyHttpUrl

    settings.cors_origins = [AnyHttpUrl("http://localhost:5173")]
    with TestClient(main.create_app(settings)) as client:
        headers = {
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "PUT",
            "Access-Control-Request-Headers": "authorization,content-type",
        }
        accepted = client.options("/api/v1/me/favorite-genres", headers=headers)
        assert accepted.status_code == 200
        assert (
            accepted.headers["Access-Control-Allow-Origin"] == "http://localhost:5173"
        )
        rejected = client.options(
            "/api/v1/me/favorite-genres",
            headers={**headers, "Origin": "https://unknown.example.com"},
        )
        assert rejected.status_code == 400
        assert "Access-Control-Allow-Origin" not in rejected.headers
