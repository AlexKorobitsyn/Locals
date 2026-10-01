from fastapi import APIRouter, Request, Response, status

from APP.core.db import SessionDependency
from APP.core.dependencies import CurrentAuthDependency
from APP.schemas.auth import LoginInput, RefreshInput, RegisterInput, TokenPair
from APP.schemas.user import UserMe
from APP.services.auth import login_user, logout_session, refresh_session, register_user

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
