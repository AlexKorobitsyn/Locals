import uvicorn

from APP.core.config import get_settings
from APP.core.logging import configure_logging
from APP.core.request_logging import RequestLoggingMiddleware
from APP.main import create_app


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    uvicorn.run(
        RequestLoggingMiddleware(create_app(settings)),
        host="0.0.0.0",
        port=settings.port,
        log_config=None,
        access_log=False,
        timeout_graceful_shutdown=settings.shutdown_timeout_seconds,
    )


if __name__ == "__main__":
    main()
