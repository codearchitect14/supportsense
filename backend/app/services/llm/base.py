from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Literal, Protocol

Role = Literal["system", "user", "assistant"]


@dataclass(frozen=True)
class LLMMessage:
    role: Role
    content: str


@dataclass(frozen=True)
class LLMResult:
    text: str
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


class LLMStream:
    """Wraps a provider's streamed text deltas; `.result` is set once fully consumed.

    Providers only learn token usage from the final chunk of their SDK's
    stream, so `finalize` is called after the underlying iterator is
    exhausted and its return value is stashed on `.result` for the caller
    (e.g. to persist token usage once streaming to the client is done).
    """

    def __init__(self, chunks: Iterator[str], finalize: Callable[[], LLMResult]) -> None:
        self._chunks = chunks
        self._finalize = finalize
        self.result: LLMResult | None = None

    def __iter__(self) -> Iterator[str]:
        for chunk in self._chunks:
            yield chunk
        self.result = self._finalize()


class LLMProvider(Protocol):
    name: str

    def complete(
        self,
        messages: list[LLMMessage],
        *,
        max_tokens: int,
        temperature: float = 0.2,
    ) -> LLMResult:
        """Runs one chat completion call. Raises LLMRateLimitError or LLMProviderError on failure."""
        ...

    def stream(
        self,
        messages: list[LLMMessage],
        *,
        max_tokens: int,
        temperature: float = 0.2,
    ) -> LLMStream:
        """Starts a streamed chat completion call.

        May raise LLMRateLimitError or LLMProviderError as soon as it's
        called (before any chunk is produced); once iteration of the
        returned LLMStream has yielded at least one chunk, callers should
        treat further errors as a mid-stream failure, not a signal to fail
        over to another provider.
        """
        ...
