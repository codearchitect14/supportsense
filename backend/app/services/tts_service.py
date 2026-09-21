from collections.abc import AsyncIterator

import edge_tts

from app.core.settings import settings


class TextToSpeechService:
    """Wraps edge-tts (free, no API key) for text-to-speech synthesis.

    edge-tts streams MP3 audio over a websocket to Microsoft's public Edge
    TTS endpoint; it requires outbound network access but no API key or
    per-request cost, matching the project's zero-cost constraint.
    """

    def __init__(self, voice: str) -> None:
        self._voice = voice

    async def stream(self, text: str) -> AsyncIterator[bytes]:
        communicate = edge_tts.Communicate(text, voice=self._voice)
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                yield chunk["data"]

    async def synthesize(self, text: str) -> bytes:
        audio = bytearray()
        async for piece in self.stream(text):
            audio.extend(piece)
        return bytes(audio)


_instance: TextToSpeechService | None = None


def get_tts_service() -> TextToSpeechService:
    global _instance
    if _instance is None:
        _instance = TextToSpeechService(settings.tts_voice)
    return _instance
