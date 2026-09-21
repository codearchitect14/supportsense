import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Literal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.models.conversation import Conversation, Message
from app.models.user import User
from app.services.conversation_summary import SUMMARY_ROLE, summarize_turns
from app.services.embedding_service import EmbeddingService
from app.services.llm.base import LLMMessage
from app.services.llm.errors import AllProvidersExhaustedError
from app.services.llm.prompt import build_system_prompt, trim_history
from app.services.llm.router import ProviderRouter
from app.services.llm.semantic_cache import SemanticCache
from app.services.retrieval_service import RetrievalService

PROVIDER_KB_DIRECT = "kb_direct"
PROVIDER_SEMANTIC_CACHE = "cache"


@dataclass(frozen=True)
class ChatReply:
    conversation_id: uuid.UUID
    message_id: uuid.UUID
    answer: str
    provider_used: str
    tokens_used: int
    matched_category: str | None


def _get_or_create_conversation(
    db: Session, *, user: User, conversation_id: uuid.UUID | None, channel: str
) -> Conversation:
    if conversation_id is None:
        conversation = Conversation(user_id=user.id, channel=channel)
        db.add(conversation)
        db.flush()
        return conversation

    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conversation is None or conversation.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="conversation not found")
    return conversation


def _build_llm_messages(
    db: Session, conversation: Conversation, context_snippets: list[str], *, exclude_message_id: uuid.UUID
) -> list[LLMMessage]:
    system_prompt = build_system_prompt(context_snippets, max_snippets=settings.llm_max_context_snippets)
    llm_messages = [LLMMessage(role="system", content=system_prompt)]

    summary = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id, Message.role == SUMMARY_ROLE)
        .order_by(Message.created_at.desc())
        .first()
    )
    if summary is not None:
        llm_messages.append(LLMMessage(role="system", content=summary.content))

    past_turns = (
        db.query(Message)
        .filter(
            Message.conversation_id == conversation.id,
            Message.role != SUMMARY_ROLE,
            Message.id != exclude_message_id,
        )
        .order_by(Message.created_at.asc())
        .all()
    )
    trimmed = trim_history(
        [LLMMessage(role=m.role, content=m.content) for m in past_turns],
        max_turns=settings.llm_history_max_turns,
    )
    llm_messages.extend(trimmed)
    return llm_messages


def _maybe_roll_up_summary(db: Session, conversation: Conversation) -> None:
    turns = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id, Message.role != SUMMARY_ROLE)
        .order_by(Message.created_at.asc())
        .all()
    )
    if len(turns) < settings.conversation_summary_trigger_turns:
        return

    keep_recent = settings.llm_history_max_turns
    older_turns = turns[:-keep_recent] if keep_recent > 0 else turns
    if not older_turns:
        return

    summary_text = summarize_turns([(m.role, m.content) for m in older_turns])

    existing_summary = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id, Message.role == SUMMARY_ROLE)
        .order_by(Message.created_at.desc())
        .first()
    )
    if existing_summary is not None:
        existing_summary.content = summary_text
    else:
        db.add(Message(conversation_id=conversation.id, role=SUMMARY_ROLE, content=summary_text))


class ChatOrchestrationService:
    """Ties retrieval, the semantic cache, and the LLM provider router into one flow.

    Token minimization order of preference, cheapest first:
      1. A high-confidence knowledge base match answers directly, no LLM call.
      2. A semantically similar question was answered recently, reuse it.
      3. Otherwise call the LLM with a compact prompt built from a few
         retrieved snippets and trimmed history.
    """

    def __init__(
        self,
        db: Session,
        embedding_service: EmbeddingService,
        retrieval_service: RetrievalService,
        semantic_cache: SemanticCache,
        provider_router: ProviderRouter,
    ) -> None:
        self._db = db
        self._embedding_service = embedding_service
        self._retrieval_service = retrieval_service
        self._semantic_cache = semantic_cache
        self._provider_router = provider_router

    def handle_message(
        self, *, user: User, conversation_id: uuid.UUID | None, text: str, channel: str = "chat"
    ) -> ChatReply:
        conversation = _get_or_create_conversation(
            self._db, user=user, conversation_id=conversation_id, channel=channel
        )
        user_message = Message(conversation_id=conversation.id, role="user", content=text)
        self._db.add(user_message)
        self._db.flush()

        query_vector = self._embedding_service.embed_query(text)
        retrieved = self._retrieval_service.search_by_vector(query_vector, top_k=settings.retrieval_top_k)

        if retrieved and retrieved[0].similarity >= settings.kb_direct_similarity_threshold:
            answer = retrieved[0].response
            provider_used = PROVIDER_KB_DIRECT
            tokens_used = 0
            matched_category = retrieved[0].category
        else:
            cached_answer = self._semantic_cache.lookup(query_vector)
            if cached_answer is not None:
                answer = cached_answer
                provider_used = PROVIDER_SEMANTIC_CACHE
                tokens_used = 0
                matched_category = retrieved[0].category if retrieved else None
            else:
                context_snippets = [entry.response for entry in retrieved]
                llm_messages = _build_llm_messages(
                    self._db, conversation, context_snippets, exclude_message_id=user_message.id
                )
                llm_messages.append(LLMMessage(role="user", content=text))

                try:
                    result = self._provider_router.complete(
                        llm_messages, max_tokens=settings.llm_max_response_tokens
                    )
                except AllProvidersExhaustedError as exc:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="the assistant is temporarily unavailable, please try again shortly",
                    ) from exc

                answer = result.text
                provider_used = result.provider
                tokens_used = result.total_tokens
                matched_category = retrieved[0].category if retrieved else None
                self._semantic_cache.store(query_vector, answer)

        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=answer,
            tokens_used=tokens_used,
            provider_used=provider_used,
        )
        self._db.add(assistant_message)
        _maybe_roll_up_summary(self._db, conversation)
        self._db.commit()
        self._db.refresh(assistant_message)

        return ChatReply(
            conversation_id=conversation.id,
            message_id=assistant_message.id,
            answer=answer,
            provider_used=provider_used,
            tokens_used=tokens_used,
            matched_category=matched_category,
        )

    def handle_message_stream(
        self, *, user: User, conversation_id: uuid.UUID | None, text: str, channel: str = "chat"
    ) -> Iterator[tuple[Literal["delta", "done"], str | ChatReply]]:
        """Same flow as handle_message, but yields ("delta", text) chunks as
        they arrive and a final ("done", ChatReply). A KB-direct answer or a
        cache hit is already fully known, so it's yielded as one delta.
        """
        conversation = _get_or_create_conversation(
            self._db, user=user, conversation_id=conversation_id, channel=channel
        )
        user_message = Message(conversation_id=conversation.id, role="user", content=text)
        self._db.add(user_message)
        self._db.flush()

        query_vector = self._embedding_service.embed_query(text)
        retrieved = self._retrieval_service.search_by_vector(query_vector, top_k=settings.retrieval_top_k)

        if retrieved and retrieved[0].similarity >= settings.kb_direct_similarity_threshold:
            answer = retrieved[0].response
            provider_used = PROVIDER_KB_DIRECT
            tokens_used = 0
            matched_category = retrieved[0].category
            yield "delta", answer
        else:
            cached_answer = self._semantic_cache.lookup(query_vector)
            if cached_answer is not None:
                answer = cached_answer
                provider_used = PROVIDER_SEMANTIC_CACHE
                tokens_used = 0
                matched_category = retrieved[0].category if retrieved else None
                yield "delta", answer
            else:
                context_snippets = [entry.response for entry in retrieved]
                llm_messages = _build_llm_messages(
                    self._db, conversation, context_snippets, exclude_message_id=user_message.id
                )
                llm_messages.append(LLMMessage(role="user", content=text))

                try:
                    provider_used, llm_stream = self._provider_router.stream(
                        llm_messages, max_tokens=settings.llm_max_response_tokens
                    )
                except AllProvidersExhaustedError as exc:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="the assistant is temporarily unavailable, please try again shortly",
                    ) from exc

                for chunk in llm_stream:
                    yield "delta", chunk

                result = llm_stream.result
                answer = result.text
                tokens_used = result.total_tokens
                matched_category = retrieved[0].category if retrieved else None
                self._semantic_cache.store(query_vector, answer)

        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=answer,
            tokens_used=tokens_used,
            provider_used=provider_used,
        )
        self._db.add(assistant_message)
        _maybe_roll_up_summary(self._db, conversation)
        self._db.commit()
        self._db.refresh(assistant_message)

        yield "done", ChatReply(
            conversation_id=conversation.id,
            message_id=assistant_message.id,
            answer=answer,
            provider_used=provider_used,
            tokens_used=tokens_used,
            matched_category=matched_category,
        )
