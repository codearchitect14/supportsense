from app.schemas.chat import ChatMessageResponse


class VoiceMessageResponse(ChatMessageResponse):
    transcript: str
    audio_base64: str
    audio_content_type: str = "audio/mpeg"
