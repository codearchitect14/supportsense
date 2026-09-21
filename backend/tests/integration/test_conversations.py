import asyncio

from app.services.tts_service import get_tts_service


def test_voice_conversation_is_tagged_with_voice_channel(client, auth_headers, kb_query, db_session):
    from app.models.conversation import Conversation

    headers = auth_headers("voicechanneluser@example.com")
    audio_bytes = asyncio.run(get_tts_service().synthesize(kb_query))

    response = client.post("/voice/message", files={"audio": ("a.mp3", audio_bytes, "audio/mpeg")}, headers=headers)
    assert response.status_code == 200

    conversation = db_session.query(Conversation).filter(Conversation.id == response.json()["conversation_id"]).first()
    assert conversation.channel == "voice"


def test_conversation_history_filters_by_channel(client, auth_headers, kb_query):
    headers = auth_headers("historyuser@example.com")

    chat_resp = client.post("/chat/message", json={"message": kb_query}, headers=headers)
    chat_conversation_id = chat_resp.json()["conversation_id"]

    audio_bytes = asyncio.run(get_tts_service().synthesize(kb_query))
    client.post("/voice/message", files={"audio": ("a.mp3", audio_bytes, "audio/mpeg")}, headers=headers)

    all_conversations = client.get("/conversations", headers=headers).json()
    assert len(all_conversations) >= 2

    chat_only = client.get("/conversations", params={"channel": "chat"}, headers=headers).json()
    voice_only = client.get("/conversations", params={"channel": "voice"}, headers=headers).json()
    assert all(c["channel"] == "chat" for c in chat_only)
    assert all(c["channel"] == "voice" for c in voice_only)
    assert any(c["id"] == chat_conversation_id for c in chat_only)


def test_conversation_history_search_finds_matching_conversation(client, auth_headers, kb_query):
    headers = auth_headers("searchuser@example.com")
    chat_resp = client.post("/chat/message", json={"message": kb_query}, headers=headers)
    conversation_id = chat_resp.json()["conversation_id"]

    search_term = " ".join(kb_query.split()[:2])
    results = client.get("/conversations", params={"search": search_term}, headers=headers).json()
    assert any(c["id"] == conversation_id for c in results)


def test_conversation_messages_are_ownership_scoped(client, auth_headers, kb_query):
    owner_headers = auth_headers("convowner@example.com")
    other_headers = auth_headers("convother@example.com")

    chat_resp = client.post("/chat/message", json={"message": kb_query}, headers=owner_headers)
    conversation_id = chat_resp.json()["conversation_id"]

    own_view = client.get(f"/conversations/{conversation_id}/messages", headers=owner_headers)
    assert own_view.status_code == 200
    assert len(own_view.json()) >= 2

    other_view = client.get(f"/conversations/{conversation_id}/messages", headers=other_headers)
    assert other_view.status_code == 404
