import pytest
from pydantic import ValidationError

from APP.core.config import Settings


def test_env_overrides_dotenv(tmp_path, monkeypatch):
    dotenv = tmp_path / ".env"
    dotenv.write_text(
        "PORT=8001\n"
        "DATABASE_URL=postgresql+asyncpg://test:test@localhost/test\n"
        "POSTGRES_DB=test\n"
    )
    monkeypatch.setenv("PORT", "8002")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    settings = Settings(_env_file=dotenv)
    assert settings.port == 8002
    assert settings.database_url.get_secret_value().endswith("/test")
    assert "test:test" not in repr(settings)


def test_database_url_is_required(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


@pytest.mark.parametrize(
    "url",
    [
        "invalid-secret",
        "sqlite+aiosqlite://",
        "postgresql://test:secret@localhost/test",
    ],
)
def test_invalid_database_url_does_not_expose_input(url):
    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None, database_url=url)
    assert url not in str(error.value)


@pytest.mark.parametrize("port", [0, 65536])
def test_invalid_port(port):
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            database_url="postgresql+asyncpg://localhost/test",
            port=port,
        )


def test_jwt_secret_is_required_and_not_exposed(monkeypatch):
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None, database_url="postgresql+asyncpg://localhost/test")
    with pytest.raises(ValidationError) as error:
        Settings(
            _env_file=None,
            database_url="postgresql+asyncpg://localhost/test",
            jwt_secret_key="short-secret",
        )
    assert "short-secret" not in str(error.value)


@pytest.mark.parametrize(
    "origin",
    [
        "https://example.com/path",
        "https://user:password@example.com",
        "https://example.com?secret=value",
    ],
)
def test_cors_rejects_non_origin_urls(origin):
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            database_url="postgresql+asyncpg://localhost/test",
            cors_origins=[origin],
        )
