import asyncio
import os
from dataclasses import dataclass
from uuid import uuid4

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool

import APP.main as main
from alembic import command
from APP.core.config import Settings

TEST_DATABASE_URL = "postgresql+asyncpg://test:test@127.0.0.1:1/test"
TEST_JWT_SECRET = "test-only-jwt-secret-never-use-in-production"


@pytest.fixture(autouse=True)
def auth_settings(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", TEST_JWT_SECRET)
    monkeypatch.setenv("BCRYPT_ROUNDS", "4")


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=None,
        database_url=TEST_DATABASE_URL,
        health_timeout_seconds=0.2,
        db_connect_timeout_seconds=0.2,
    )


@dataclass
class CatalogDatabase:
    engine: AsyncEngine
    settings: Settings
    schema: str

    def execute(self, statement: str, parameters: dict | None = None):
        async def run():
            async with self.engine.begin() as connection:
                result = await connection.execute(text(statement), parameters or {})
                return result.mappings().all() if result.returns_rows else None

        return asyncio.run(run())

    def migrate(self, direction: str, revision: str):
        async def run():
            async with self.engine.begin() as connection:

                def apply(sync_connection):
                    config = Config("alembic.ini")
                    config.attributes["connection"] = sync_connection
                    getattr(command, direction)(config, revision)

                await connection.run_sync(apply)

        asyncio.run(run())


@pytest.fixture
def catalog_db(monkeypatch):
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to run catalog and auth integration checks")
    schema = "test_" + uuid4().hex
    bootstrap = create_async_engine(url, poolclass=NullPool)

    async def create_schema():
        async with bootstrap.begin() as connection:
            await connection.execute(text(f'CREATE SCHEMA "{schema}"'))

    asyncio.run(create_schema())
    # NullPool позволяет использовать один engine в разных тестовых event loop.
    engine = create_async_engine(
        url,
        poolclass=NullPool,
        connect_args={"server_settings": {"search_path": schema}},
    )
    database = CatalogDatabase(
        engine=engine,
        settings=Settings(_env_file=None, database_url=url, bcrypt_rounds=4),
        schema=schema,
    )
    try:
        database.migrate("upgrade", "head")
        yield database
    finally:

        async def cleanup():
            await engine.dispose()
            async with bootstrap.begin() as connection:
                await connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
            await bootstrap.dispose()

        asyncio.run(cleanup())


@pytest.fixture
def api_client(catalog_db, monkeypatch):
    monkeypatch.setattr(main, "create_engine", lambda _: catalog_db.engine)
    with TestClient(main.create_app(catalog_db.settings)) as client:
        yield client


@pytest.fixture
def account(api_client):
    def create(name="listener"):
        credentials = {"email": f"{name}@example.com", "password": "test-password-long"}
        response = api_client.post(
            "/api/v1/auth/register", json={**credentials, "display_name": name}
        )
        assert response.status_code == 201, response.text
        user = response.json()
        tokens = api_client.post("/api/v1/auth/login", json=credentials)
        assert tokens.status_code == 200, tokens.text
        return user, {"Authorization": "Bearer " + tokens.json()["access_token"]}

    return create
