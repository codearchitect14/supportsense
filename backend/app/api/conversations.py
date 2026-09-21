import uuid
from datetime import date, datetime, time, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.models.conversation import Conversation, Message
from app.models.user import User
from app.schemas.conversation import ConversationSummary, MessageOut
from app.services.conversation_summary import SUMMARY_ROLE

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationSummary])
@limiter.limit("60/minute")
def list_conversations(
    request: Request,
    channel: str | None = Query(default=None, pattern="^(chat|voice)$"),
    start_date: date | None = None,
    end_date: date | None = None,
    search: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ConversationSummary]:
    last_message = (
        db.query(
            Message.conversation_id.label("conversation_id"),
            func.max(Message.created_at).label("last_message_at"),
        )
        .filter(Message.role != SUMMARY_ROLE)
        .group_by(Message.conversation_id)
        .subquery()
    )

    query = (
        db.query(
            Conversation,
            func.count(Message.id).filter(Message.role != SUMMARY_ROLE).label("message_count"),
            last_message.c.last_message_at,
        )
        .outerjoin(Message, Message.conversation_id == Conversation.id)
        .outerjoin(last_message, last_message.c.conversation_id == Conversation.id)
        .filter(Conversation.user_id == current_user.id)
    )

    if channel:
        query = query.filter(Conversation.channel == channel)
    if start_date:
        query = query.filter(Conversation.started_at >= datetime.combine(start_date, time.min, tzinfo=timezone.utc))
    if end_date:
        query = query.filter(Conversation.started_at <= datetime.combine(end_date, time.max, tzinfo=timezone.utc))
    if search:
        query = query.filter(
            Conversation.id.in_(db.query(Message.conversation_id).filter(Message.content.ilike(f"%{search}%")))
        )

    query = query.group_by(Conversation.id, last_message.c.last_message_at)
    query = query.order_by(last_message.c.last_message_at.desc().nulls_last(), Conversation.started_at.desc())
    rows = query.offset(offset).limit(limit).all()

    summaries = []
    for conversation, message_count, last_message_at in rows:
        preview_message = (
            db.query(Message)
            .filter(Message.conversation_id == conversation.id, Message.role != SUMMARY_ROLE)
            .order_by(Message.created_at.desc())
            .first()
        )
        preview = preview_message.content[:140] if preview_message else None
        summaries.append(
            ConversationSummary(
                id=conversation.id,
                channel=conversation.channel,
                started_at=conversation.started_at,
                ended_at=conversation.ended_at,
                message_count=message_count,
                last_message_preview=preview,
                last_message_at=last_message_at,
            )
        )
    return summaries


@router.get("/{conversation_id}/messages", response_model=list[MessageOut])
@limiter.limit("60/minute")
def get_conversation_messages(
    request: Request,
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Message]:
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conversation is None or conversation.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="conversation not found")

    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id, Message.role != SUMMARY_ROLE)
        .order_by(Message.created_at.asc())
        .all()
    )
