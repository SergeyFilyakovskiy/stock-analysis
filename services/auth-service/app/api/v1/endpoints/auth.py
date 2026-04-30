from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.api.v1.schemas.profile import ProfileResponse
from app.application.commands.login_user import LoginUserCommand, LoginUserHandler
from app.application.commands.logout_user import LogoutUserCommand, LogoutUserHandler
from app.application.commands.refresh_token import RefreshTokenCommand, RefreshTokenHandler
from app.application.commands.register_user import RegisterUserCommand, RegisterUserHandler
from app.application.queries.get_user_profile import GetUserProfileHandler, GetUserProfileQuery
from app.application.services.token_service import TokenService
from app.core.dependencies import (
    get_access_token,
    get_login_handler,
    get_logout_handler,
    get_profile_handler,
    get_refresh_handler,
    get_register_handler,
)
from app.domain.exceptions import (
    InvalidCredentialsError,
    InvalidTokenError,
    TooManyAttemptsError,
    UserAlreadyExistsError,
    UserInactiveError,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    body:          RegisterRequest,
    handler:       RegisterUserHandler = Depends(get_register_handler),
    login_handler: LoginUserHandler    = Depends(get_login_handler),
):
    try:
        await handler.handle(RegisterUserCommand(
            email=body.email,
            password=body.password,
            first_name=body.first_name,
            last_name=body.last_name,
        ))
        tokens = await login_handler.handle(
            LoginUserCommand(email=body.email, password=body.password)
        )
        return TokenResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
        )
    except UserAlreadyExistsError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(e))
    except ValueError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(
    body:    LoginRequest,
    handler: LoginUserHandler = Depends(get_login_handler),
):
    try:
        tokens = await handler.handle(
            LoginUserCommand(email=body.email, password=body.password)
        )
        return TokenResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
        )
    except InvalidCredentialsError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    except TooManyAttemptsError:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many attempts, try later")
    except UserInactiveError:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Account is deactivated")


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body:    RefreshRequest,
    handler: RefreshTokenHandler = Depends(get_refresh_handler),
):
    try:
        tokens = await handler.handle(
            RefreshTokenCommand(refresh_token=body.refresh_token)
        )
        return TokenResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
        )
    except InvalidTokenError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    access_token: str               = Depends(get_access_token),
    handler:      LogoutUserHandler = Depends(get_logout_handler),
):
    try:
        payload = TokenService().decode_token(access_token)
        await handler.handle(LogoutUserCommand(
            access_token=access_token,
            user_id=UUID(payload["sub"]),
        ))
    except InvalidTokenError:
        pass


@router.get("/me", response_model=ProfileResponse)
async def get_me(
    access_token: str                  = Depends(get_access_token),
    handler:      GetUserProfileHandler = Depends(get_profile_handler),
):
    try:
        payload = TokenService().decode_token(access_token)
        dto     = await handler.handle(
            GetUserProfileQuery(user_id=UUID(payload["sub"]))
        )
        return ProfileResponse(**dto.__dict__)
    except InvalidTokenError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(e))