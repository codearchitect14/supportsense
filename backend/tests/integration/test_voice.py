import asyncio

from app.services.tts_service import get_tts_service


def test_voice_message_transcribes_real_speech_accurately(client, auth_headers, kb_query):
    # Spoken text must be something the assistant can actually answer without
    # a real LLM key configured, so it's the exact KB-direct query used
    # elsewhere, not an arbitrary paraphrase (which would 503: no confident
    # KB match and no LLM provider available to fall back to).
    headers = auth_headers("voiceuser@example.com")
    audio_bytes = asyncio.run(get_tts_service().synthesize(kb_query))

    response = client.post("/voice/message", files={"audio": ("a.mp3", audio_bytes, "audio/mpeg")}, headers=headers)
    assert response.status_code == 200
    transcript = response.json()["transcript"].lower()
    meaningful_words = [w.strip(".,?!").lower() for w in kb_query.split() if len(w) > 3]
    assert any(word in transcript for word in meaningful_words)


def test_voice_message_rejects_viewer_role(client, auth_headers):
    headers = auth_headers("voiceviewer@example.com", role="viewer")
    audio_bytes = asyncio.run(get_tts_service().synthesize("hello"))
    response = client.post("/voice/message", files={"audio": ("a.mp3", audio_bytes, "audio/mpeg")}, headers=headers)
    assert response.status_code == 403


def test_voice_message_returns_synthesized_audio(client, auth_headers, kb_query):
    headers = auth_headers("voiceaudiouser@example.com")
    audio_bytes = asyncio.run(get_tts_service().synthesize(kb_query))

    response = client.post("/voice/message", files={"audio": ("a.mp3", audio_bytes, "audio/mpeg")}, headers=headers)
    body = response.json()
    assert len(body["audio_base64"]) > 100
    assert body["audio_content_type"] == "audio/mpeg"
