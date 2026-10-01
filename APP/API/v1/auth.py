from fastapi import APIRouter, HTTPException, Request, Response, status
from starlette.responses import JSONResponse

from APP.core.browser_auth import (
    REFRESH_COOKIE_NAME,
    browser_token,
    clear_refresh_cookie,
    require_browser_origin,
)
from APP.core.db import SessionDependency
from APP.core.dependencies import CurrentAuthDependency
from APP.schemas.auth import (
    BrowserToken,
    LoginInput,
    RefreshInput,
    RegisterInput,
    TokenPair,
)
from APP.schemas.user import UserMe
from APP.services.auth import (
    login_user,
    logout_refresh_session,
    logout_session,
    refresh_session,
    register_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserMe, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterInput, request: Request, session: SessionDependency
) -> UserMe:
    user = await register_user(session, payload, request.app.state.settings)
    return UserMe.model_validate(user)


@router.post("/login", response_model=TokenPair)
async def login(
    payload: LoginInput,
    request: Request,
    session: SessionDependency,
    response: Response,
) -> TokenPair:
    response.headers["Cache-Control"] = "no-store"
    return await login_user(session, payload, request.app.state.settings)


@router.post("/refresh", response_model=TokenPair)
async def refresh(
    payload: RefreshInput,
    request: Request,
    session: SessionDependency,
    response: Response,
) -> TokenPair:
    response.headers["Cache-Control"] = "no-store"
    return await refresh_session(
        session, payload.refresh_token.get_secret_value(), request.app.state.settings
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    identity: CurrentAuthDependency, session: SessionDependency
) -> Response:
    await logout_session(session, identity.session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/browser/login", response_model=BrowserToken)
async def browser_login(
    payload: LoginInput,
    request: Request,
    session: SessionDependency,
    response: Response,
) -> BrowserToken:
    require_browser_origin(request)
    settings = request.app.state.settings
    pair = await login_user(session, payload, settings)
    return browser_token(pair, response, settings)


@router.post("/browser/refresh", response_model=BrowserToken)
async def browser_refresh(
    request: Request, session: SessionDependency, response: Response
) -> BrowserToken | Response:
    require_browser_origin(request)
    settings = request.app.state.settings
    token = request.cookies.get(REFRESH_COOKIE_NAME)
    try:
        if token is None:
            raise HTTPException(
                status_code=401, detail="Invalid or expired credentials"
            )
        pair = await refresh_session(session, token, settings)
    except HTTPException as error:
        if error.status_code != 401:
            raise
        failure = JSONResponse({"detail": error.detail}, status_code=401)
        clear_refresh_cookie(failure, settings)
        return failure
    return browser_token(pair, response, settings)


@router.post("/browser/logout", status_code=status.HTTP_204_NO_CONTENT)
async def browser_logout(request: Request, session: SessionDependency) -> Response:
    require_browser_origin(request)
    token = request.cookies.get(REFRESH_COOKIE_NAME)
    if token is not None:
        await logout_refresh_session(session, token)
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    clear_refresh_cookie(response, request.app.state.settings)
    return response
