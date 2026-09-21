import uuid
from datetime import datetime

from pydantic import BaseModel


class ConversationSummary(BaseModel):
    id: uuid.UUID
    channel: str
    started_at: datetime
    ended_at: datetime | None
    message_count: int
    last_message_preview: str | None
    last_message_at: datetime | None


class MessageOut(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    tokens_used: int | None
    provider_used: str | None
    feedback: bool | None
    created_at: datetime

    model_config = {"from_attributes": True}
