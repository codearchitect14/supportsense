import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.rate_limit import limiter
from app.core.settings import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    PasswordResetRequestResponse,
    RefreshRequest,
    SignupRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserOut,
)
from app.services import auth_service
from app.services.audit_service import log_event

logger = logging.getLogger("app.auth")

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_PATH = "/auth"


def _set_refresh_cookie(response: Response, raw_refresh_token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=raw_refresh_token,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path=REFRESH_COOKIE_PATH,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path=REFRESH_COOKIE_PATH)


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def signup(request: Request, payload: SignupRequest, db: Session = Depends(get_db)) -> User:
    user = auth_service.signup(db, email=payload.email, password=payload.password, full_name=payload.full_name)
    log_event(db, user_id=user.id, action="signup", resource=f"user:{user.id}")
    return user


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = auth_service.authenticate(db, email=form_data.username, password=form_data.password)
    access_token, expires_in = auth_service.issue_access_token(user)
    raw_refresh_token = auth_service.issue_refresh_token(db, user)
    _set_refresh_cookie(response, raw_refresh_token)

    log_event(db, user_id=user.id, action="login", resource=f"user:{user.id}")
    return TokenResponse(access_token=access_token, expires_in=expires_in, user=user)


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("30/minute")
def refresh(
    request: Request,
    response: Response,
    payload: RefreshRequest | None = None,
    db: Session = Depends(get_db),
) -> TokenResponse:
    raw_refresh_token = (payload.refresh_token if payload else None) or request.cookies.get(REFRESH_COOKIE_NAME)
    if not raw_refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing refresh token")

    user, new_raw_refresh_token = auth_service.rotate_refresh_token(db, raw_refresh_token)
    access_token, expires_in = auth_service.issue_access_token(user)
    _set_refresh_cookie(response, new_raw_refresh_token)

    return TokenResponse(access_token=access_token, expires_in=expires_in, user=user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("30/minute")
def logout(
    request: Request,
    response: Response,
    payload: RefreshRequest | None = None,
    db: Session = Depends(get_db),
) -> None:
    raw_refresh_token = (payload.refresh_token if payload else None) or request.cookies.get(REFRESH_COOKIE_NAME)
    if raw_refresh_token:
        auth_service.revoke_refresh_token(db, raw_refresh_token)
    _clear_refresh_cookie(response)


@router.post("/password-reset/request", response_model=PasswordResetRequestResponse)
@limiter.limit("5/minute")
def request_password_reset(
    request: Request, payload: PasswordResetRequest, db: Session = Depends(get_db)
) -> PasswordResetRequestResponse:
    raw_token = auth_service.request_password_reset(db, email=payload.email)

    generic_message = "if that email is registered, a password reset link has been sent"
    if raw_token is None:
        return PasswordResetRequestResponse(message=generic_message)

    logger.info("password reset requested", extra={"email": payload.email})

    # No transactional email provider is wired up yet, so the raw token is
    # only ever handed back outside production, to keep the reset flow
    # testable end to end without leaking it to a real deployment.
    return PasswordResetRequestResponse(
        message=generic_message,
        reset_token=None if settings.is_production else raw_token,
    )


@router.post("/password-reset/confirm", response_model=UserOut)
@limiter.limit("10/minute")
def confirm_password_reset(
    request: Request, payload: PasswordResetConfirm, db: Session = Depends(get_db)
) -> User:
    user = auth_service.confirm_password_reset(db, raw_token=payload.token, new_password=payload.new_password)
    log_event(db, user_id=user.id, action="password_reset", resource=f"user:{user.id}")
    return user


@router.get("/me", response_model=UserOut)
@limiter.limit("60/minute")
def read_current_user(request: Request, current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.patch("/me", response_model=UserOut)
@limiter.limit("20/minute")
def update_current_user(
    request: Request,
    payload: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    user = auth_service.update_profile(db, user=current_user, full_name=payload.full_name)
    log_event(db, user_id=user.id, action="profile_update", resource=f"user:{user.id}")
    return user


@router.post("/change-password", response_model=UserOut)
@limiter.limit("10/minute")
def change_password(
    request: Request,
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    user = auth_service.change_password(
        db, user=current_user, current_password=payload.current_password, new_password=payload.new_password
    )
    log_event(db, user_id=user.id, action="password_change", resource=f"user:{user.id}")
    return user
