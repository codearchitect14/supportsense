from unittest.mock import MagicMock

import pytest

from app.db.redis_client import get_redis
from app.services.llm.base import LLMMessage, LLMResult
from app.services.llm.errors import AllProvidersExhaustedError, LLMRateLimitError
from app.services.llm.quota import ProviderLimit, QuotaTracker
from app.services.llm.router import ProviderRouter


@pytest.fixture(autouse=True)
def _flush_redis():
    get_redis().flushdb()
    yield


def _fake_provider(name: str, result: LLMResult | None = None, raises: Exception | None = None):
    provider = MagicMock()
    provider.name = name
    if raises is not None:
        provider.complete = MagicMock(side_effect=raises)
    else:
        provider.complete = MagicMock(return_value=result)
    return provider


def _router(providers: list, limits: dict | None = None) -> ProviderRouter:
    tracker = QuotaTracker(get_redis())
    default_limits = {p.name: ProviderLimit(requests_per_minute=30, requests_per_day=1000) for p in providers}
    return ProviderRouter(providers, limits or default_limits, tracker)


def test_prefers_primary_when_healthy():
    primary = _fake_provider("groq", LLMResult("a", "groq", "m", 1, 1))
    secondary = _fake_provider("gemini", LLMResult("b", "gemini", "m", 1, 1))
    result = _router([primary, secondary]).complete([LLMMessage(role="user", content="hi")], max_tokens=10)
    assert result.provider == "groq"
    secondary.complete.assert_not_called()


def test_fails_over_to_secondary_on_primary_rate_limit():
    primary = _fake_provider("groq", raises=LLMRateLimitError("boom"))
    secondary = _fake_provider("gemini", LLMResult("fallback", "gemini", "m", 1, 1))
    result = _router([primary, secondary]).complete([LLMMessage(role="user", content="hi")], max_tokens=10)
    assert result.provider == "gemini"


def test_marks_primary_in_cooldown_after_rate_limit():
    redis_client = get_redis()
    primary = _fake_provider("groq", raises=LLMRateLimitError("boom"))
    secondary = _fake_provider("gemini", LLMResult("fallback", "gemini", "m", 1, 1))
    _router([primary, secondary]).complete([LLMMessage(role="user", content="hi")], max_tokens=10)
    assert redis_client.exists("llm:quota:groq:cooldown") == 1


def test_proactively_skips_provider_once_minute_budget_is_used():
    primary = _fake_provider("groq", LLMResult("a", "groq", "m", 1, 1))
    secondary = _fake_provider("gemini", LLMResult("b", "gemini", "m", 1, 1))
    limits = {"groq": ProviderLimit(requests_per_minute=1, requests_per_day=1000), "gemini": ProviderLimit(30, 1000)}
    router = _router([primary, secondary], limits)

    first = router.complete([LLMMessage(role="user", content="hi")], max_tokens=10)
    second = router.complete([LLMMessage(role="user", content="hi")], max_tokens=10)

    assert first.provider == "groq"
    assert second.provider == "gemini"


def test_raises_when_every_provider_is_exhausted():
    primary = _fake_provider("groq", raises=LLMRateLimitError("boom"))
    secondary = _fake_provider("gemini", raises=LLMRateLimitError("boom too"))
    with pytest.raises(AllProvidersExhaustedError):
        _router([primary, secondary]).complete([LLMMessage(role="user", content="hi")], max_tokens=10)


def test_empty_provider_list_raises_immediately():
    with pytest.raises(AllProvidersExhaustedError):
        _router([]).complete([LLMMessage(role="user", content="hi")], max_tokens=10)
