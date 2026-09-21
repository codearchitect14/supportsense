import pytest

from app.db.redis_client import get_redis
from app.services.llm.semantic_cache import SemanticCache


@pytest.fixture
def cache():
    redis_client = get_redis()
    redis_client.flushdb()
    return SemanticCache(redis_client, namespace="test:cache", ttl_seconds=60, similarity_threshold=0.9, max_entries=3)


def test_miss_on_empty_cache(cache):
    assert cache.lookup([1.0, 0.0, 0.0]) is None


def test_hit_on_identical_vector(cache):
    cache.store([1.0, 0.0, 0.0], "cached answer")
    assert cache.lookup([1.0, 0.0, 0.0]) == "cached answer"


def test_hit_on_near_identical_vector(cache):
    cache.store([1.0, 0.0, 0.0], "cached answer")
    assert cache.lookup([0.99, 0.01, 0.0]) == "cached answer"


def test_miss_on_dissimilar_vector(cache):
    cache.store([1.0, 0.0, 0.0], "cached answer")
    assert cache.lookup([0.0, 1.0, 0.0]) is None


def test_enforces_max_entries_bound(cache):
    redis_client = get_redis()
    for i in range(5):
        cache.store([0.0, 0.0, float(i + 1)], f"answer {i}")
    assert redis_client.scard("test:cache:index") <= 3
