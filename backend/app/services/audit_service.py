import uuid

from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def log_event(db: Session, *, user_id: uuid.UUID | None, action: str, resource: str) -> None:
    db.add(AuditLog(user_id=user_id, action=action, resource=resource))
    db.commit()
