from collections.abc import Iterator

from groq import Groq, RateLimitError

from app.services.llm.base import LLMMessage, LLMResult, LLMStream
from app.services.llm.errors import LLMProviderError, LLMRateLimitError

# This SDK version doesn't support stream_options={"include_usage": True},
# so streamed responses have no exact token counts from the API. Token
# counts on streamed results are therefore a rough char-count estimate,
# unlike complete(), which always reports exact usage from the API.
_CHARS_PER_TOKEN_ESTIMATE = 4


class GroqProvider:
    name = "groq"

    def __init__(self, api_key: str, model: str) -> None:
        self._client = Groq(api_key=api_key)
        self._model = model

    def complete(
        self,
        messages: list[LLMMessage],
        *,
        max_tokens: int,
        temperature: float = 0.2,
    ) -> LLMResult:
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": m.role, "content": m.content} for m in messages],
                max_tokens=max_tokens,
                temperature=temperature,
            )
        except RateLimitError as exc:
            raise LLMRateLimitError(str(exc)) from exc
        except Exception as exc:  # noqa: BLE001 - any SDK failure should fail over, not crash the request
            raise LLMProviderError(str(exc)) from exc

        choice = response.choices[0]
        usage = response.usage
        return LLMResult(
            text=choice.message.content or "",
            provider=self.name,
            model=self._model,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
        )

    def stream(
        self,
        messages: list[LLMMessage],
        *,
        max_tokens: int,
        temperature: float = 0.2,
    ) -> LLMStream:
        try:
            sdk_stream = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": m.role, "content": m.content} for m in messages],
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
            )
        except RateLimitError as exc:
            raise LLMRateLimitError(str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            raise LLMProviderError(str(exc)) from exc

        prompt_chars = sum(len(m.content) for m in messages)
        state = {"text": ""}

        def chunks() -> Iterator[str]:
            try:
                for event in sdk_stream:
                    delta = event.choices[0].delta.content if event.choices else None
                    if delta:
                        state["text"] += delta
                        yield delta
            except Exception as exc:  # noqa: BLE001 - stream already started, surface as a mid-stream failure
                raise LLMProviderError(str(exc)) from exc

        def finalize() -> LLMResult:
            return LLMResult(
                text=state["text"],
                provider=self.name,
                model=self._model,
                prompt_tokens=prompt_chars // _CHARS_PER_TOKEN_ESTIMATE,
                completion_tokens=len(state["text"]) // _CHARS_PER_TOKEN_ESTIMATE,
            )

        return LLMStream(chunks(), finalize)
