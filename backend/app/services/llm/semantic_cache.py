import json
import math
import uuid

import redis


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class SemanticCache:
    """Redis-backed cache of (query embedding -> answer) to skip LLM calls
    for questions that are semantically close to one recently answered.

    This class does not compute embeddings itself: callers pass in an
    already-embedded query vector, produced by whatever embedding model the
    rest of the application uses (see the EmbeddingService built alongside
    the retrieval-augmented chat engine), so the cache stays decoupled from
    a specific model choice.
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        *,
        namespace: str = "llm:semantic_cache",
        ttl_seconds: int = 3600,
        similarity_threshold: float = 0.92,
        max_entries: int = 500,
    ) -> None:
        self._redis = redis_client
        self._namespace = namespace
        self._ttl_seconds = ttl_seconds
        self._similarity_threshold = similarity_threshold
        self._max_entries = max_entries

    def _index_key(self) -> str:
        return f"{self._namespace}:index"

    def _entry_key(self, entry_id: str) -> str:
        return f"{self._namespace}:entry:{entry_id}"

    def lookup(self, query_vector: list[float]) -> str | None:
        entry_ids = self._redis.smembers(self._index_key())

        best_answer: str | None = None
        best_score = 0.0
        stale_ids: list[str] = []

        for entry_id in entry_ids:
            raw = self._redis.get(self._entry_key(entry_id))
            if raw is None:
                stale_ids.append(entry_id)
                continue

            data = json.loads(raw)
            score = _cosine_similarity(query_vector, data["vector"])
            if score > best_score:
                best_score = score
                best_answer = data["answer"]

        if stale_ids:
            self._redis.srem(self._index_key(), *stale_ids)

        if best_score >= self._similarity_threshold:
            return best_answer
        return None

    def store(self, query_vector: list[float], answer: str) -> None:
        entry_id = uuid.uuid4().hex
        payload = json.dumps({"vector": query_vector, "answer": answer})

        pipe = self._redis.pipeline()
        pipe.set(self._entry_key(entry_id), payload, ex=self._ttl_seconds)
        pipe.sadd(self._index_key(), entry_id)
        pipe.expire(self._index_key(), self._ttl_seconds)
        pipe.execute()

        self._enforce_max_entries()

    def _enforce_max_entries(self) -> None:
        entry_ids = list(self._redis.smembers(self._index_key()))
        overflow = len(entry_ids) - self._max_entries
        if overflow <= 0:
            return

        excess = entry_ids[:overflow]
        pipe = self._redis.pipeline()
        for entry_id in excess:
            pipe.delete(self._entry_key(entry_id))
        pipe.srem(self._index_key(), *excess)
        pipe.execute()
