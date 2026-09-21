import io
import logging
import threading

from faster_whisper import WhisperModel
from faster_whisper.audio import decode_audio

from app.core.settings import settings

logger = logging.getLogger("app.stt")

WHISPER_SAMPLE_RATE = 16000


class SpeechToTextService:
    """Wraps faster-whisper for local, CPU speech-to-text transcription.

    Accepts audio in whatever container/codec the client recorded (webm,
    ogg, wav, mp3, ...): decode_audio shells out to the bundled ffmpeg/PyAV
    decoder rather than assuming a specific format.
    """

    def __init__(self, model_size: str, device: str, compute_type: str) -> None:
        logger.info("loading whisper model", extra={"model_size": model_size})
        self._model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, audio_bytes: bytes) -> str:
        if not audio_bytes:
            return ""

        try:
            audio = decode_audio(io.BytesIO(audio_bytes), sampling_rate=WHISPER_SAMPLE_RATE)
        except Exception:
            logger.exception("failed to decode audio for transcription")
            return ""

        if audio.size == 0:
            return ""

        segments, _info = self._model.transcribe(audio, language="en", vad_filter=True)
        return " ".join(segment.text.strip() for segment in segments).strip()


_instance: SpeechToTextService | None = None
_lock = threading.Lock()


def get_stt_service() -> SpeechToTextService:
    global _instance
    if _instance is None:
        with _lock:
            if _instance is None:
                _instance = SpeechToTextService(
                    settings.whisper_model_size, settings.whisper_device, settings.whisper_compute_type
                )
    return _instance
