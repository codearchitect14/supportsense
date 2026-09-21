from collections.abc import Iterator

from google import genai
from google.genai import errors as genai_errors
from google.genai import types as genai_types

from app.services.llm.base import LLMMessage, LLMResult, LLMStream
from app.services.llm.errors import LLMProviderError, LLMRateLimitError

_ROLE_MAP = {"user": "user", "assistant": "model"}


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str, model: str) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

    @staticmethod
    def _build_request(
        messages: list[LLMMessage], *, max_tokens: int, temperature: float
    ) -> tuple[list[genai_types.Content], genai_types.GenerateContentConfig]:
        system_instruction = "\n".join(m.content for m in messages if m.role == "system") or None
        contents = [
            genai_types.Content(role=_ROLE_MAP[m.role], parts=[genai_types.Part(text=m.content)])
            for m in messages
            if m.role in _ROLE_MAP
        ]
        config = genai_types.GenerateContentConfig(
            system_instruction=system_instruction,
            max_output_tokens=max_tokens,
            temperature=temperature,
        )
        return contents, config

    def complete(
        self,
        messages: list[LLMMessage],
        *,
        max_tokens: int,
        temperature: float = 0.2,
    ) -> LLMResult:
        contents, config = self._build_request(messages, max_tokens=max_tokens, temperature=temperature)

        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=contents,
                config=config,
            )
        except genai_errors.ClientError as exc:
            if exc.code == 429:
                raise LLMRateLimitError(str(exc)) from exc
            raise LLMProviderError(str(exc)) from exc
        except genai_errors.APIError as exc:
            raise LLMProviderError(str(exc)) from exc
        except Exception as exc:  # noqa: BLE001 - any SDK failure should fail over, not crash the request
            raise LLMProviderError(str(exc)) from exc

        usage = response.usage_metadata
        return LLMResult(
            text=response.text or "",
            provider=self.name,
            model=self._model,
            prompt_tokens=usage.prompt_token_count if usage and usage.prompt_token_count else 0,
            completion_tokens=usage.candidates_token_count if usage and usage.candidates_token_count else 0,
        )

    def stream(
        self,
        messages: list[LLMMessage],
        *,
        max_tokens: int,
        temperature: float = 0.2,
    ) -> LLMStream:
        contents, config = self._build_request(messages, max_tokens=max_tokens, temperature=temperature)

        try:
            sdk_stream = self._client.models.generate_content_stream(
                model=self._model,
                contents=contents,
                config=config,
            )
        except genai_errors.ClientError as exc:
            if exc.code == 429:
                raise LLMRateLimitError(str(exc)) from exc
            raise LLMProviderError(str(exc)) from exc
        except genai_errors.APIError as exc:
            raise LLMProviderError(str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            raise LLMProviderError(str(exc)) from exc

        state = {"text": "", "prompt_tokens": 0, "completion_tokens": 0}

        def chunks() -> Iterator[str]:
            try:
                for event in sdk_stream:
                    delta = event.text or ""
                    if delta:
                        state["text"] += delta
                        yield delta
                    usage = event.usage_metadata
                    if usage:
                        state["prompt_tokens"] = usage.prompt_token_count or state["prompt_tokens"]
                        state["completion_tokens"] = usage.candidates_token_count or state["completion_tokens"]
            except genai_errors.APIError as exc:
                raise LLMProviderError(str(exc)) from exc
            except Exception as exc:  # noqa: BLE001 - stream already started, surface as a mid-stream failure
                raise LLMProviderError(str(exc)) from exc

        def finalize() -> LLMResult:
            return LLMResult(
                text=state["text"],
                provider=self.name,
                model=self._model,
                prompt_tokens=state["prompt_tokens"],
                completion_tokens=state["completion_tokens"],
            )

        return LLMStream(chunks(), finalize)
