from collections.abc import Callable

from fastapi import Depends, HTTPException, Query, WebSocketException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def _resolve_user(token: str | None, db: Session) -> User | None:
    if token is None:
        return None
    try:
        payload = decode_access_token(token)
    except JWTError:
        return None

    user_id = payload.get("sub")
    if user_id is None:
        return None

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        return None
    return user


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    user = _resolve_user(token, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_user_ws(
    token: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> User:
    """WebSocket auth: browsers can't set Authorization headers on the
    handshake, so the access token is passed as a query parameter instead.
    """
    user = _resolve_user(token, db)
    if user is None:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="could not validate credentials")
    return user


def require_roles(*allowed_roles: str) -> Callable[[User], User]:
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.name not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="insufficient permissions")
        return current_user

    return dependency


def require_roles_ws(*allowed_roles: str) -> Callable[[User], User]:
    def dependency(current_user: User = Depends(get_current_user_ws)) -> User:
        if current_user.role.name not in allowed_roles:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="insufficient permissions")
        return current_user

    return dependency
