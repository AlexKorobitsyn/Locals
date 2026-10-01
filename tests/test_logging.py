import json
import logging

from APP.core.logging import JsonFormatter, configure_logging


def test_logging_is_json_in_stdout_without_duplicate_handlers(capsys):
    configure_logging("INFO")
    configure_logging("INFO")
    logging.getLogger("uvicorn.error").info(
        "Приложение готово", extra={"request_id": "test"}
    )
    captured = capsys.readouterr()
    lines = captured.out.splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["message"] == "Приложение готово"
    assert payload["request_id"] == "test"
    assert payload["level"] == "INFO"
    assert payload["timestamp"].endswith("+00:00")
    assert not captured.err


def test_exception_is_encoded_on_one_json_line():
    try:
        raise RuntimeError("test failure")
    except RuntimeError:
        record = logging.LogRecord(
            "test", logging.ERROR, __file__, 1, "Operation failed", (), None
        )
        import sys

        record.exc_info = sys.exc_info()
    rendered = JsonFormatter().format(record)
    assert len(rendered.splitlines()) == 1
    assert "RuntimeError: test failure" in json.loads(rendered)["exception"]
