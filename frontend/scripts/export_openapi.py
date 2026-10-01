"""Экспорт HTTP-контракта без запуска lifespan и подключения к БД."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from APP.core.config import Settings  # noqa: E402
from APP.main import create_app  # noqa: E402

settings = Settings(
    _env_file=None,
    database_url="postgresql+asyncpg://contract:contract@127.0.0.1/contract",
    jwt_secret_key="contract-export-only-not-a-runtime-secret",
    s3_endpoint_url=None,
    s3_public_endpoint_url=None,
    s3_access_key=None,
    s3_secret_key=None,
)
sys.stdout.write(json.dumps(create_app(settings).openapi(), ensure_ascii=False))
