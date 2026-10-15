import json
import logging
import os
from datetime import UTC, datetime
from logging.config import dictConfig

from APP.core.request_logging import request_log_context

STANDARD_RECORD_FIELDS = frozenset(logging.makeLogRecord({}).__dict__) | {
    "message",
    "asctime",
}


class JsonFormatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service_name = os.environ.get("SERVICE_NAME", "locals-backend")

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service.name": self.service_name,
        }
        payload.update(
            (key, value)
            for key, value in record.__dict__.items()
            if key not in STANDARD_RECORD_FIELDS
        )
        context = request_log_context.get()
        if context is not None:
            payload.update(
                request_id=context.request_id,
                method=context.method,
                path=context.path,
            )
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(level: str) -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {"json": {"()": JsonFormatter}},
            "handlers": {
                "stdout": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                    "formatter": "json",
                }
            },
            "root": {"handlers": ["stdout"], "level": level},
            "loggers": {
                "uvicorn": {"handlers": [], "propagate": True, "level": level},
                "uvicorn.error": {"handlers": [], "propagate": True, "level": level},
                "uvicorn.access": {"handlers": [], "propagate": True, "level": level},
                "sqlalchemy.engine": {
                    "handlers": [],
                    "propagate": True,
                    "level": "WARNING",
                },
            },
        }
    )
