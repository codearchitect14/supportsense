import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import UpdateUserRoleRequest, UserOut
from app.services import auth_service
from app.services.audit_service import log_event

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
@limiter.limit("30/minute")
def list_users(
    request: Request,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_roles("admin")),
) -> list[User]:
    return db.query(User).order_by(User.created_at).all()


@router.patch("/{user_id}/role", response_model=UserOut)
@limiter.limit("20/minute")
def update_user_role(
    request: Request,
    user_id: uuid.UUID,
    payload: UpdateUserRoleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> User:
    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="cannot change your own role")

    user = auth_service.update_user_role(db, user_id=user_id, role_name=payload.role)
    log_event(db, user_id=current_user.id, action="role_change", resource=f"user:{user.id}:{payload.role}")
    return user
