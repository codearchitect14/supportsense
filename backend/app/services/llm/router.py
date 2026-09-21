import logging
from collections.abc import Iterator

from app.services.llm.base import LLMMessage, LLMProvider, LLMResult, LLMStream
from app.services.llm.errors import AllProvidersExhaustedError, LLMProviderError, LLMRateLimitError
from app.services.llm.quota import ProviderLimit, QuotaTracker

logger = logging.getLogger("app.llm.router")


class ProviderRouter:
    """Routes chat completions across providers in priority order.

    The first provider in `providers` is the primary. On every call the
    router tries providers in that fixed order, skipping any that are over
    budget or in cooldown, so it automatically "switches back" to the
    primary as soon as its quota window resets, with no sticky failover
    state to manage.
    """

    def __init__(
        self,
        providers: list[LLMProvider],
        limits: dict[str, ProviderLimit],
        quota_tracker: QuotaTracker,
    ) -> None:
        # An empty list is a valid (if degraded) configuration: this MVP is
        # meant to run with no LLM keys configured yet, in which case every
        # call falls through to AllProvidersExhaustedError and callers can
        # still serve KB-direct/cached answers that need no LLM at all.
        self._providers = providers
        self._limits = limits
        self._quota_tracker = quota_tracker

    def complete(
        self,
        messages: list[LLMMessage],
        *,
        max_tokens: int,
        temperature: float = 0.2,
    ) -> LLMResult:
        last_error: Exception | None = None

        for provider in self._providers:
            limit = self._limits.get(provider.name)
            if limit is not None and not self._quota_tracker.has_budget(provider.name, limit):
                logger.info("skipping provider over budget", extra={"provider": provider.name})
                continue

            try:
                result = provider.complete(messages, max_tokens=max_tokens, temperature=temperature)
            except LLMRateLimitError as exc:
                logger.warning("provider rate limited, failing over", extra={"provider": provider.name})
                self._quota_tracker.mark_rate_limited(provider.name)
                last_error = exc
                continue
            except LLMProviderError as exc:
                logger.warning("provider call failed, failing over", extra={"provider": provider.name})
                last_error = exc
                continue

            self._quota_tracker.record_usage(provider.name)
            logger.info(
                "provider handled request",
                extra={"provider": provider.name, "total_tokens": result.total_tokens},
            )
            return result

        raise AllProvidersExhaustedError("all configured LLM providers are unavailable") from last_error

    def stream(
        self,
        messages: list[LLMMessage],
        *,
        max_tokens: int,
        temperature: float = 0.2,
    ) -> tuple[str, LLMStream]:
        """Picks a provider and starts streaming. Returns (provider_name, LLMStream).

        Failover only happens before the first chunk is produced; once
        streaming has started, a mid-stream error propagates to the caller
        instead of silently switching providers under a partially-sent
        response.
        """
        last_error: Exception | None = None

        for provider in self._providers:
            limit = self._limits.get(provider.name)
            if limit is not None and not self._quota_tracker.has_budget(provider.name, limit):
                logger.info("skipping provider over budget", extra={"provider": provider.name})
                continue

            try:
                llm_stream = provider.stream(messages, max_tokens=max_tokens, temperature=temperature)
                chunk_source = iter(llm_stream)
                first_chunk = next(chunk_source, None)
            except LLMRateLimitError as exc:
                logger.warning("provider rate limited, failing over", extra={"provider": provider.name})
                self._quota_tracker.mark_rate_limited(provider.name)
                last_error = exc
                continue
            except LLMProviderError as exc:
                logger.warning("provider stream failed, failing over", extra={"provider": provider.name})
                last_error = exc
                continue

            self._quota_tracker.record_usage(provider.name)
            logger.info("provider streaming request", extra={"provider": provider.name})

            def rejoin(first: str | None, rest: Iterator[str]) -> Iterator[str]:
                if first is not None:
                    yield first
                # Draining `rest` (the inner LLMStream's own generator) to
                # exhaustion runs its `self.result = finalize()` line before
                # it raises StopIteration, so llm_stream.result is already
                # populated by the time this generator itself finishes.
                yield from rest

            llm_stream_with_first = LLMStream(rejoin(first_chunk, chunk_source), lambda: llm_stream.result)
            return provider.name, llm_stream_with_first

        raise AllProvidersExhaustedError("all configured LLM providers are unavailable") from last_error
