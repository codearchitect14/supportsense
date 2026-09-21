import base64
import json
import logging
import time

from fastapi import APIRouter, Depends, File, Request, UploadFile, WebSocket, WebSocketDisconnect
from starlette.concurrency import run_in_threadpool

from app.api.chat import CHAT_ROLES, get_chat_service
from app.core.deps import require_roles, require_roles_ws
from app.core.rate_limit import limiter
from app.core.settings import settings
from app.models.user import User
from app.schemas.voice import VoiceMessageResponse
from app.services.chat_service import ChatOrchestrationService
from app.services.stt_service import get_stt_service
from app.services.tts_service import get_tts_service

logger = logging.getLogger("app.voice")

router = APIRouter(prefix="/voice", tags=["voice"])

# A WS utterance buffer this large (roughly a couple of minutes of compressed
# audio) is a sign the client never sent an end_utterance event; finalize
# rather than let memory grow unbounded.
MAX_UTTERANCE_BUFFER_BYTES = 10 * 1024 * 1024


@router.post("/message", response_model=VoiceMessageResponse)
@limiter.limit("15/minute")
async def send_voice_message(
    request: Request,
    audio: UploadFile = File(...),
    current_user: User = Depends(require_roles(*CHAT_ROLES)),
    chat_service: ChatOrchestrationService = Depends(get_chat_service),
) -> VoiceMessageResponse:
    audio_bytes = await audio.read()

    stt_service = get_stt_service()
    transcript = await run_in_threadpool(stt_service.transcribe, audio_bytes)
    if not transcript:
        transcript = ""

    reply = await run_in_threadpool(
        chat_service.handle_message,
        user=current_user,
        conversation_id=None,
        text=transcript or "(no speech detected)",
        channel="voice",
    )

    tts_service = get_tts_service()
    answer_audio = await tts_service.synthesize(reply.answer)

    return VoiceMessageResponse(
        conversation_id=reply.conversation_id,
        message_id=reply.message_id,
        answer=reply.answer,
        provider_used=reply.provider_used,
        tokens_used=reply.tokens_used,
        matched_category=reply.matched_category,
        transcript=transcript,
        audio_base64=base64.b64encode(answer_audio).decode("ascii"),
    )


@router.websocket("/stream")
async def stream_voice(
    websocket: WebSocket,
    current_user: User = Depends(require_roles_ws(*CHAT_ROLES)),
    chat_service: ChatOrchestrationService = Depends(get_chat_service),
) -> None:
    """Voice pipeline over one WebSocket connection, one utterance at a time:

    client -> binary audio chunks -> {"event": "end_utterance"} text frame
    server -> periodic {"type": "transcript", "final": false} partials while
              audio is arriving, then {"type": "transcript", "final": true},
              then {"type": "answer_delta"} chunks reusing the same
              ChatOrchestrationService streaming path as text chat, then
              binary audio chunks of the synthesized reply, then
              {"type": "done"}.
    """
    await websocket.accept()
    stt_service = get_stt_service()
    tts_service = get_tts_service()

    buffer = bytearray()
    last_partial_at = 0.0
    conversation_id: str | None = None

    async def finalize_utterance() -> None:
        nonlocal buffer, conversation_id
        if not buffer:
            return

        transcript = await run_in_threadpool(stt_service.transcribe, bytes(buffer))
        buffer = bytearray()
        await websocket.send_json({"type": "transcript", "final": True, "text": transcript})

        if not transcript:
            await websocket.send_json({"type": "error", "message": "no speech detected"})
            return

        try:
            for event_type, data in chat_service.handle_message_stream(
                user=current_user, conversation_id=conversation_id, text=transcript, channel="voice"
            ):
                if event_type == "delta":
                    await websocket.send_json({"type": "answer_delta", "text": data})
                else:
                    conversation_id = data.conversation_id
                    async for audio_chunk in tts_service.stream(data.answer):
                        await websocket.send_bytes(audio_chunk)
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
        except Exception:  # noqa: BLE001 - keep the socket alive for the next utterance
            logger.exception("voice pipeline failed")
            await websocket.send_json({"type": "error", "message": "the assistant could not respond"})

    try:
        while True:
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                break

            if (audio_chunk := message.get("bytes")) is not None:
                buffer.extend(audio_chunk)

                if len(buffer) >= MAX_UTTERANCE_BUFFER_BYTES:
                    await finalize_utterance()
                    last_partial_at = time.monotonic()
                    continue

                now = time.monotonic()
                if buffer and now - last_partial_at >= settings.voice_partial_transcribe_seconds:
                    last_partial_at = now
                    partial_text = await run_in_threadpool(stt_service.transcribe, bytes(buffer))
                    await websocket.send_json({"type": "transcript", "final": False, "text": partial_text})

            elif (raw_text := message.get("text")) is not None:
                try:
                    control = json.loads(raw_text)
                except ValueError:
                    await websocket.send_json({"type": "error", "message": "invalid control message"})
                    continue

                event = control.get("event")
                if event == "end_utterance":
                    await finalize_utterance()
                    last_partial_at = time.monotonic()
                elif event == "reset":
                    buffer = bytearray()
                else:
                    await websocket.send_json({"type": "error", "message": f"unknown event: {event}"})
    except WebSocketDisconnect:
        return
