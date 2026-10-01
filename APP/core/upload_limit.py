from starlette.datastructures import Headers
from starlette.formparsers import MultiPartException
from starlette.responses import JSONResponse

from APP.core.constants import UPLOAD_CHUNK_BYTES


class UploadLimitMiddleware:
    def __init__(self, app, settings):
        self.app = app
        self.settings = settings

    async def __call__(self, scope, receive, send):
        path = scope.get("path", "")
        if (
            scope["type"] != "http"
            or scope.get("method") != "POST"
            or path not in ("/api/v1/media/images", "/api/v1/media/audio")
        ):
            return await self.app(scope, receive, send)
        maximum = (
            self.settings.audio_max_bytes
            if path.endswith("/audio")
            else self.settings.image_max_bytes
        ) + UPLOAD_CHUNK_BYTES
        content_length = Headers(scope=scope).get("content-length")
        try:
            oversized = content_length is not None and int(content_length) > maximum
        except ValueError:
            oversized = True
        if oversized:
            return await JSONResponse(
                {"detail": "Request exceeds the upload limit"}, status_code=413
            )(scope, receive, send)
        size, exceeded = 0, False

        async def limited_receive():
            nonlocal size, exceeded
            message = await receive()
            size += len(message.get("body", b""))
            if size > maximum:
                exceeded = True
                # Multipart-парсер закроет временные файлы при этом исключении.
                raise MultiPartException("Request exceeds the upload limit")
            return message

        async def limited_send(message):
            if exceeded and message["type"] == "http.response.start":
                message["status"] = 413
            await send(message)

        await self.app(scope, limited_receive, limited_send)
