"""Synthetic load test: fires concurrent chat requests against a primary
provider with a deliberately tight quota, and confirms the provider router
actually fails over to the secondary once that quota is exhausted, rather
than the endpoint degrading or erroring out under load.

Skipped by default (see pyproject.toml's addopts). Run explicitly with:
    pytest -m load tests/load/test_chat_fallback_load.py
"""

import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest

from app.api import chat as chat_api
from app.db.redis_client import get_redis
from app.db.session import SessionLocal
from app.main import app
from app.services.chat_service import ChatOrchestrationService
from app.services.embedding_service import get_embedding_service
from app.services.llm.base import LLMResult
from app.services.llm.quota import ProviderLimit, QuotaTracker
from app.services.llm.router import ProviderRouter
from app.services.retrieval_service import RetrievalService

CONCURRENT_REQUESTS = 20
PRIMARY_QUOTA_PER_MINUTE = 5


class _FakeProvider:
    def __init__(self, name: str) -> None:
        self.name = name

    def complete(self, messages, *, max_tokens, temperature=0.2):
        return LLMResult(
            text=f"answer from {self.name}", provider=self.name, model="test", prompt_tokens=5, completion_tokens=5
        )


class _AlwaysMissCache:
    """Every generated query below is a near-duplicate template differing only
    by a UUID, so their embeddings are similar enough to trip the real
    SemanticCache's similarity threshold after the first couple of requests.
    This test is exercising the provider router's fallback under concurrent
    load, not the cache, so it uses a cache that never hits.
    """

    def lookup(self, query_vector):
        return None

    def store(self, query_vector, answer):
        pass


@pytest.mark.load
def test_provider_fallback_triggers_under_concurrent_load(client, auth_headers):
    headers = auth_headers("loadtestuser@example.com")

    get_redis().flushdb()
    router = ProviderRouter(
        [_FakeProvider("groq"), _FakeProvider("gemini")],
        {
            "groq": ProviderLimit(requests_per_minute=PRIMARY_QUOTA_PER_MINUTE, requests_per_day=10_000),
            "gemini": ProviderLimit(requests_per_minute=1000, requests_per_day=100_000),
        },
        QuotaTracker(get_redis()),
    )

    def override():
        # Generator dependency so FastAPI closes this session after each
        # request; a plain `return` would leak a connection per request.
        db = SessionLocal()
        try:
            embedding_service = get_embedding_service()
            yield ChatOrchestrationService(
                db, embedding_service, RetrievalService(db, embedding_service), _AlwaysMissCache(), router
            )
        finally:
            db.close()

    app.dependency_overrides[chat_api.get_chat_service] = override

    def _send_one(_: int) -> str:
        # A unique, unanswerable-from-the-KB query per request so every call
        # actually reaches the provider router instead of hitting the cache.
        query = f"zzz totally novel unique load test query {uuid.uuid4()}"
        response = client.post("/chat/message", json={"message": query}, headers=headers)
        assert response.status_code == 200
        return response.json()["provider_used"]

    try:
        with ThreadPoolExecutor(max_workers=8) as executor:
            providers_used = list(executor.map(_send_one, range(CONCURRENT_REQUESTS)))
    finally:
        app.dependency_overrides.pop(chat_api.get_chat_service, None)

    assert len(providers_used) == CONCURRENT_REQUESTS
    assert "groq" in providers_used, "primary provider should handle at least the first few requests"
    assert "gemini" in providers_used, "secondary provider should take over once the primary's quota is spent"
