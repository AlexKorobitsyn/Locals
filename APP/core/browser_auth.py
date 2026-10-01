from fastapi import HTTPException, Request, Response

from APP.core.config import Settings
from APP.core.security import decode_access_token
from APP.schemas.auth import BrowserToken, TokenPair

REFRESH_COOKIE_NAME = "locals_refresh"
REFRESH_COOKIE_PATH = "/api/v1/auth/browser"
CSRF_HEADER_NAME = "X-CSRF-Protection"
CSRF_HEADER_VALUE = "1"


def require_browser_origin(request: Request) -> None:
    settings = request.app.state.settings
    origins = {str(origin).rstrip("/") for origin in settings.browser_allowed_origins}
    if (
        request.headers.get("origin") not in origins
        or request.headers.get(CSRF_HEADER_NAME) != CSRF_HEADER_VALUE
        or request.headers.get("sec-fetch-site") == "cross-site"
    ):
        raise HTTPException(status_code=403, detail="Browser origin is not allowed")


def browser_token(
    pair: TokenPair, response: Response, settings: Settings
) -> BrowserToken:
    response.headers["Cache-Control"] = "no-store"
    response.set_cookie(
        REFRESH_COOKIE_NAME,
        pair.refresh_token,
        max_age=pair.refresh_expires_in,
        path=REFRESH_COOKIE_PATH,
        httponly=True,
        secure=settings.browser_cookie_secure,
        samesite="lax",
    )
    claims = decode_access_token(pair.access_token, settings)
    return BrowserToken(
        access_token=pair.access_token,
        expires_in=pair.expires_in,
        user_id=claims.user_id,
        session_id=claims.session_id,
    )


def clear_refresh_cookie(response: Response, settings: Settings) -> None:
    response.headers["Cache-Control"] = "no-store"
    response.delete_cookie(
        REFRESH_COOKIE_NAME,
        path=REFRESH_COOKIE_PATH,
        httponly=True,
        secure=settings.browser_cookie_secure,
        samesite="lax",
    )
