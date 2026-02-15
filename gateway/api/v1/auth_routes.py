from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from gateway.dependencies.auth import get_current_user
from shared.database.session import get_db
from shared.schemas.user_schema import (
    LogoutResponse,
    RefreshTokenRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from services.auth_service.auth_service import AuthService, get_auth_service

router = APIRouter()

@router.post("/register", response_model=UserResponse)
def register(
    payload: UserCreate,
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        user = auth_service.create_user(
            db=db,
            email=payload.email,
            password=payload.password
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc)
        ) from exc

    return user


@router.post("/login", response_model=TokenResponse)
def login(
    payload: UserLogin,
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
):
    user = auth_service.authenticate_user(
        db=db,
        email=payload.email,
        password=payload.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token, expires_in, refresh_token, refresh_expires_in = auth_service.create_token_pair(user)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
        refresh_expires_in=refresh_expires_in,
    )


@router.post("/logout", response_model=LogoutResponse)
def logout(
    user=Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    auth_service.revoke_token(user["token"])
    return LogoutResponse(message="Successfully logged out")


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        access_token, expires_in, refresh_token_value, refresh_expires_in = (
            auth_service.refresh_access_token(db=db, refresh_token=payload.refresh_token)
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_value,
        expires_in=expires_in,
        refresh_expires_in=refresh_expires_in,
    )
