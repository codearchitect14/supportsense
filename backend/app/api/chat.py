import logging

from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.deps import require_roles, require_roles_ws
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.models.user import User
from app.schemas.chat import ChatMessageRequest, ChatMessageResponse
from app.services.chat_service import ChatOrchestrationService
from app.services.embedding_service import get_embedding_service
from app.services.llm.factory import get_provider_router, get_semantic_cache
from app.services.retrieval_service import RetrievalService

logger = logging.getLogger("app.chat")

router = APIRouter(prefix="/chat", tags=["chat"])

# Only roles with chat access (per the Phase 3 role matrix) may use the assistant.
CHAT_ROLES = ("admin", "agent")


def get_chat_service(db: Session = Depends(get_db)) -> ChatOrchestrationService:
    embedding_service = get_embedding_service()
    retrieval_service = RetrievalService(db, embedding_service)
    return ChatOrchestrationService(
        db,
        embedding_service,
        retrieval_service,
        get_semantic_cache(),
        get_provider_router(),
    )


@router.post("/message", response_model=ChatMessageResponse)
@limiter.limit("20/minute")
def send_message(
    request: Request,
    payload: ChatMessageRequest,
    current_user: User = Depends(require_roles(*CHAT_ROLES)),
    chat_service: ChatOrchestrationService = Depends(get_chat_service),
) -> ChatMessageResponse:
    reply = chat_service.handle_message(
        user=current_user, conversation_id=payload.conversation_id, text=payload.message
    )
    return ChatMessageResponse(
        conversation_id=reply.conversation_id,
        message_id=reply.message_id,
        answer=reply.answer,
        provider_used=reply.provider_used,
        tokens_used=reply.tokens_used,
        matched_category=reply.matched_category,
    )


@router.websocket("/stream")
async def stream_chat(
    websocket: WebSocket,
    current_user: User = Depends(require_roles_ws(*CHAT_ROLES)),
    chat_service: ChatOrchestrationService = Depends(get_chat_service),
) -> None:
    await websocket.accept()

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                payload = ChatMessageRequest.model_validate_json(raw)
            except ValueError:
                await websocket.send_json({"type": "error", "message": "invalid request payload"})
                continue

            try:
                for event_type, data in chat_service.handle_message_stream(
                    user=current_user, conversation_id=payload.conversation_id, text=payload.message
                ):
                    if event_type == "delta":
                        await websocket.send_json({"type": "delta", "text": data})
                    else:
                        await websocket.send_json(
                            {
                                "type": "done",
                                "conversation_id": str(data.conversation_id),
                                "message_id": str(data.message_id),
                                "provider_used": data.provider_used,
                                "tokens_used": data.tokens_used,
                                "matched_category": data.matched_category,
                            }
                        )
            except Exception:  # noqa: BLE001 - keep the socket alive for the next message
                logger.exception("chat stream failed")
                await websocket.send_json({"type": "error", "message": "the assistant could not respond"})
    except WebSocketDisconnect:
        return
