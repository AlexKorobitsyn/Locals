import asyncio
import json
import logging
from uuid import UUID

import pytest

from APP.core.logging import configure_logging
from APP.core.request_logging import RequestLoggingMiddleware, request_log_context


async def run_request(app, path="/tracks", headers=()):
    messages = []

    async def receive():
        raise AssertionError("Logging middleware must not read the request body")

    async def send(message):
        messages.append(message)

    await RequestLoggingMiddleware(app)(
        {"type": "http", "method": "GET", "path": path, "headers": headers},
        receive,
        send,
    )
    return messages


async def respond(scope, receive, send):
    logging.getLogger("APP.test").info("Inside request")
    await asyncio.sleep(0)
    await send({"type": "http.response.start", "status": 200, "headers": []})
    await send({"type": "http.response.body", "body": b"first", "more_body": True})
    await send({"type": "http.response.body", "body": b"last"})


def test_proxy_id_streaming_response_and_context_cleanup(capsys):
    configure_logging("INFO")
    request_id = "a" * 32
    messages = asyncio.run(
        run_request(respond, headers=[(b"x-request-id", request_id.encode())])
    )
    logs = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert len(logs) == 2
    assert all(log["request_id"] == request_id for log in logs)
    assert all(log["method"] == "GET" and log["path"] == "/tracks" for log in logs)
    access = logs[-1]
    assert access["logger"] == "APP.http"
    assert access["status"] == 200
    assert access["duration_ms"] >= 0
    assert access["response_completed"] is True
    assert dict(messages[0]["headers"])[b"x-request-id"] == request_id.encode()
    assert [message.get("body") for message in messages[1:]] == [b"first", b"last"]
    assert request_log_context.get() is None


@pytest.mark.parametrize("header", [b"", b"\xff", b"x" * 4096, b"not-a-request-id"])
def test_invalid_proxy_id_uses_generated_uuid(header, capsys):
    configure_logging("INFO")
    messages = asyncio.run(run_request(respond, headers=[(b"x-request-id", header)]))
    request_id = dict(messages[0]["headers"])[b"x-request-id"].decode()
    assert UUID(hex=request_id).version == 4
    logs = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert all(log["request_id"] == request_id for log in logs)


def test_concurrent_requests_keep_separate_contexts(capsys):
    configure_logging("INFO")

    async def run():
        await asyncio.gather(
            run_request(respond, path="/first", headers=[(b"x-request-id", b"a" * 32)]),
            run_request(
                respond, path="/second", headers=[(b"x-request-id", b"b" * 32)]
            ),
        )
        assert request_log_context.get() is None

    asyncio.run(run())
    logs = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert len(logs) == 4
    for log in logs:
        expected_id = "a" * 32 if log["path"] == "/first" else "b" * 32
        assert log["request_id"] == expected_id


def test_unhandled_error_response_logged_and_exception_reraised(capsys):
    configure_logging("INFO")

    async def fail(scope, receive, send):
        await send({"type": "http.response.start", "status": 500, "headers": []})
        await send({"type": "http.response.body", "body": b"Internal Server Error"})
        raise RuntimeError("test failure")

    async def run():
        with pytest.raises(RuntimeError, match="test failure"):
            await run_request(fail)
        assert request_log_context.get() is None

    asyncio.run(run())
    access = json.loads(capsys.readouterr().out)
    assert access["status"] == 500
    assert access["level"] == "ERROR"
    assert access["error_type"] == "RuntimeError"
    assert access["response_completed"] is True


def test_entrypoint_wraps_application_and_disables_duplicate_access_logs(
    monkeypatch, settings
):
    import APP.__main__ as entrypoint

    calls = []
    monkeypatch.setattr(entrypoint, "get_settings", lambda: settings)
    monkeypatch.setattr(entrypoint, "configure_logging", lambda _: None)
    monkeypatch.setattr(
        entrypoint.uvicorn, "run", lambda app, **kwargs: calls.append((app, kwargs))
    )
    entrypoint.main()
    app, options = calls[0]
    assert isinstance(app, RequestLoggingMiddleware)
    assert options["access_log"] is False
