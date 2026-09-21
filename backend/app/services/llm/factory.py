import logging
from functools import lru_cache

from app.core.settings import settings
from app.db.redis_client import get_redis
from app.services.llm.gemini_provider import GeminiProvider
from app.services.llm.groq_provider import GroqProvider
from app.services.llm.quota import ProviderLimit, QuotaTracker
from app.services.llm.router import ProviderRouter
from app.services.llm.semantic_cache import SemanticCache

logger = logging.getLogger("app.llm.factory")


@lru_cache
def get_provider_router() -> ProviderRouter:
    # Both providers are optional: this project is meant to run at zero
    # cost with no keys configured yet, so a missing key skips that
    # provider instead of crashing every chat request (including the
    # KB-direct and cache paths, which need no LLM at all).
    providers = []
    if settings.groq_api_key:
        providers.append(GroqProvider(api_key=settings.groq_api_key, model=settings.groq_model))
    else:
        logger.warning("GROQ_API_KEY is not set, the groq provider is disabled")
    if settings.gemini_api_key:
        providers.append(GeminiProvider(api_key=settings.gemini_api_key, model=settings.gemini_model))
    else:
        logger.warning("GEMINI_API_KEY is not set, the gemini provider is disabled")

    limits = {
        "groq": ProviderLimit(
            requests_per_minute=settings.groq_requests_per_minute,
            requests_per_day=settings.groq_requests_per_day,
        ),
        "gemini": ProviderLimit(
            requests_per_minute=settings.gemini_requests_per_minute,
            requests_per_day=settings.gemini_requests_per_day,
        ),
    }
    quota_tracker = QuotaTracker(get_redis())
    return ProviderRouter(providers, limits, quota_tracker)


@lru_cache
def get_semantic_cache() -> SemanticCache:
    return SemanticCache(
        get_redis(),
        ttl_seconds=settings.semantic_cache_ttl_seconds,
        similarity_threshold=settings.semantic_cache_similarity_threshold,
        max_entries=settings.semantic_cache_max_entries,
    )
