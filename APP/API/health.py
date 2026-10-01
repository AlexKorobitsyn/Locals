import logging

from asyncpg import PostgresError
from fastapi import APIRouter, Request, Response, status
from sqlalchemy.exc import SQLAlchemyError

from APP.core.db import check_database
from APP.schemas.health import HealthOut, ReadinessOut, VersionOut

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", response_model=HealthOut)
async def liveness() -> HealthOut:
    return HealthOut()


@router.get(
    "/ready",
    response_model=ReadinessOut,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ReadinessOut}},
)
async def readiness(request: Request, response: Response) -> ReadinessOut:
    try:
        await check_database(
            request.app.state.engine,
            request.app.state.settings.health_timeout_seconds,
        )
    except (SQLAlchemyError, PostgresError, OSError, TimeoutError) as exc:
        # Параметры подключения и текст ошибки не попадают в ответ и логи.
        logger.warning(
            "Database readiness check failed",
            extra={"error_type": type(exc).__name__},
        )
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return ReadinessOut(status="unavailable", database="unavailable")
    return ReadinessOut(status="ok", database="ok")


@router.get("/version", response_model=VersionOut)
async def version(request: Request, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return VersionOut(release_id=request.app.state.settings.release_id)
