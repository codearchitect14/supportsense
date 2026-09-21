import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    generate_opaque_token,
    hash_opaque_token,
    hash_password,
    verify_password,
)
from app.core.settings import settings
from app.models.token import PasswordResetToken, RefreshToken
from app.models.user import Role, User


def _get_role(db: Session, name: str) -> Role:
    role = db.query(Role).filter(Role.name == name).first()
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"role '{name}' is not configured",
        )
    return role


def signup(db: Session, *, email: str, password: str, full_name: str) -> User:
    existing = db.query(User).filter(User.email == email).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email is already registered")

    default_role = _get_role(db, "viewer")
    user = User(
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
        role_id=default_role.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, *, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="account is disabled")
    return user


def issue_access_token(user: User) -> tuple[str, int]:
    token = create_access_token(user.id, user.role.name)
    return token, settings.access_token_expire_minutes * 60


def issue_refresh_token(db: Session, user: User) -> str:
    raw_token, token_hash = generate_opaque_token()
    now = datetime.now(timezone.utc)
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=now + timedelta(days=settings.refresh_token_expire_days),
            created_at=now,
        )
    )
    db.commit()
    return raw_token


def rotate_refresh_token(db: Session, raw_token: str) -> tuple[User, str]:
    """Validates a refresh token, revokes it, and issues a new one (rotation)."""
    token_hash = hash_opaque_token(raw_token)
    record = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()

    now = datetime.now(timezone.utc)
    if record is None or record.revoked_at is not None or record.expires_at < now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid or expired refresh token")

    user = db.query(User).filter(User.id == record.user_id).first()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid or expired refresh token")

    record.revoked_at = now
    db.commit()

    new_raw_token = issue_refresh_token(db, user)
    return user, new_raw_token


def revoke_refresh_token(db: Session, raw_token: str) -> None:
    token_hash = hash_opaque_token(raw_token)
    record = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    if record is not None and record.revoked_at is None:
        record.revoked_at = datetime.now(timezone.utc)
        db.commit()


def request_password_reset(db: Session, *, email: str) -> str | None:
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        return None

    raw_token, token_hash = generate_opaque_token()
    now = datetime.now(timezone.utc)
    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=now + timedelta(minutes=settings.password_reset_token_expire_minutes),
            created_at=now,
        )
    )
    db.commit()
    return raw_token


def confirm_password_reset(db: Session, *, raw_token: str, new_password: str) -> User:
    token_hash = hash_opaque_token(raw_token)
    record = db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == token_hash).first()

    now = datetime.now(timezone.utc)
    if record is None or record.used_at is not None or record.expires_at < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid or expired reset token")

    user = db.query(User).filter(User.id == record.user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid or expired reset token")

    user.hashed_password = hash_password(new_password)
    record.used_at = now
    db.query(RefreshToken).filter(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None)).update(
        {"revoked_at": now}
    )
    db.commit()
    return user


def update_profile(db: Session, *, user: User, full_name: str) -> User:
    user.full_name = full_name
    db.commit()
    db.refresh(user)
    return user


def change_password(db: Session, *, user: User, current_password: str, new_password: str) -> User:
    if not verify_password(current_password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="current password is incorrect")

    user.hashed_password = hash_password(new_password)
    now = datetime.now(timezone.utc)
    db.query(RefreshToken).filter(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None)).update(
        {"revoked_at": now}
    )
    db.commit()
    db.refresh(user)
    return user


def update_user_role(db: Session, *, user_id: uuid.UUID, role_name: str) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")

    role = _get_role(db, role_name)
    user.role_id = role.id
    db.commit()
    db.refresh(user)
    return user
