import time
from dataclasses import dataclass

import redis


@dataclass(frozen=True)
class ProviderLimit:
    requests_per_minute: int
    requests_per_day: int


class QuotaTracker:
    """Tracks per-provider request counts in Redis and enforces per-minute/per-day budgets.

    Counters are keyed by the current minute/day window, so once a window
    rolls over the provider's counter resets on its own with no extra
    bookkeeping needed to "switch back" to it.
    """

    def __init__(self, redis_client: redis.Redis, namespace: str = "llm:quota") -> None:
        self._redis = redis_client
        self._namespace = namespace

    def _minute_key(self, provider: str, now: float) -> str:
        return f"{self._namespace}:{provider}:minute:{int(now // 60)}"

    def _day_key(self, provider: str, now: float) -> str:
        return f"{self._namespace}:{provider}:day:{int(now // 86400)}"

    def _cooldown_key(self, provider: str) -> str:
        return f"{self._namespace}:{provider}:cooldown"

    def has_budget(self, provider: str, limit: ProviderLimit) -> bool:
        if self._redis.exists(self._cooldown_key(provider)):
            return False

        now = time.time()
        minute_count = int(self._redis.get(self._minute_key(provider, now)) or 0)
        day_count = int(self._redis.get(self._day_key(provider, now)) or 0)
        return minute_count < limit.requests_per_minute and day_count < limit.requests_per_day

    def record_usage(self, provider: str) -> None:
        now = time.time()
        minute_key = self._minute_key(provider, now)
        day_key = self._day_key(provider, now)

        pipe = self._redis.pipeline()
        pipe.incr(minute_key)
        pipe.expire(minute_key, 70)
        pipe.incr(day_key)
        pipe.expire(day_key, 90_000)
        pipe.execute()

    def mark_rate_limited(self, provider: str, cooldown_seconds: int = 60) -> None:
        """Reactive guard: honors a 429 even if our proactive counters disagreed."""
        self._redis.set(self._cooldown_key(provider), "1", ex=cooldown_seconds)
