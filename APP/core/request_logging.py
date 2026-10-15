import logging
import re
from contextvars import ContextVar
from http import HTTPStatus
from time import perf_counter
from typing import NamedTuple
from uuid import uuid4

from starlette.types import ASGIApp, Message, Receive, Scope, Send

MILLISECONDS_PER_SECOND = 1000
DURATION_DECIMAL_PLACES = 3
REQUEST_ID_HEADER = b"x-request-id"
REQUEST_ID_PATTERN = re.compile(rb"[0-9a-fA-F]{32}")
logger = logging.getLogger("APP.http")


class RequestLogContext(NamedTuple):
    request_id: str
    method: str
    path: str


request_log_context: ContextVar[RequestLogContext | None] = ContextVar(
    "request_log_context",
    default=None,
)


class RequestLoggingMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = None
        for name, value in scope.get("headers", []):
            if name.lower() == REQUEST_ID_HEADER:
                if REQUEST_ID_PATTERN.fullmatch(value):
                    request_id = value.decode("ascii").lower()
                break
        if not request_id:
            request_id = uuid4().hex
        context = RequestLogContext(
            request_id=request_id,
            method=scope["method"],
            path=scope["path"],
        )
        token = request_log_context.set(context)
        started_at = perf_counter()
        completed_at: float | None = None
        status_code: int | None = None
        error_type: str | None = None

        async def send_with_logging(message: Message) -> None:
            nonlocal status_code, completed_at
            if message["type"] == "http.response.start":
                status_code = message["status"]
                message = dict(message)
                headers = [
                    (name, value)
                    for name, value in message.get("headers", [])
                    if name.lower() != REQUEST_ID_HEADER
                ]
                headers.append((REQUEST_ID_HEADER, context.request_id.encode("ascii")))
                message["headers"] = headers
            await send(message)
            if message["type"] == "http.response.body" and not message.get(
                "more_body", False
            ):
                completed_at = perf_counter()

        try:
            await self.app(scope, receive, send_with_logging)
        except Exception as exc:
            error_type = type(exc).__name__
            raise
        finally:
            try:
                finished_at = (
                    completed_at if completed_at is not None else perf_counter()
                )
                duration_ms = round(
                    (finished_at - started_at) * MILLISECONDS_PER_SECOND,
                    DURATION_DECIMAL_PLACES,
                )
                extra = {
                    "status": status_code,
                    "duration_ms": duration_ms,
                    "response_completed": completed_at is not None,
                }
                if error_type is not None:
                    extra["error_type"] = error_type
                if error_type is not None or (
                    status_code is not None
                    and status_code >= HTTPStatus.INTERNAL_SERVER_ERROR
                ):
                    level = logging.ERROR
                elif completed_at is None or (
                    status_code is not None and status_code >= HTTPStatus.BAD_REQUEST
                ):
                    level = logging.WARNING
                else:
                    level = logging.INFO
                logger.log(
                    level,
                    "HTTP request finished",
                    extra=extra,
                )
            finally:
                request_log_context.reset(token)
