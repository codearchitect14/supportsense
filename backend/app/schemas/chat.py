import uuid

from pydantic import BaseModel, Field

from app.schemas.base import StrictRequestModel


class ChatMessageRequest(StrictRequestModel):
    conversation_id: uuid.UUID | None = None
    message: str = Field(min_length=1, max_length=4000)


class ChatMessageResponse(BaseModel):
    conversation_id: uuid.UUID
    message_id: uuid.UUID
    answer: str
    provider_used: str
    tokens_used: int
    matched_category: str | None


class MessageFeedbackRequest(StrictRequestModel):
    helpful: bool
