from app.services.llm.base import LLMMessage

BASE_SYSTEM_PROMPT = (
    "You are a customer support assistant. Answer only using the context "
    "snippets below. If they do not contain the answer, say you are not "
    "sure and offer to escalate. Be concise."
)


def build_system_prompt(context_snippets: list[str], *, max_snippets: int = 3) -> str:
    """Builds a compact system prompt from the top retrieved knowledge base snippets.

    Capping the snippet count (rather than sending the full corpus) is the
    main lever for keeping prompt tokens low on every LLM call.
    """
    selected = context_snippets[:max_snippets]
    if not selected:
        return BASE_SYSTEM_PROMPT

    numbered = "\n".join(f"[{i + 1}] {snippet.strip()}" for i, snippet in enumerate(selected))
    return f"{BASE_SYSTEM_PROMPT}\n\nContext:\n{numbered}"


def trim_history(turns: list[LLMMessage], *, max_turns: int = 4) -> list[LLMMessage]:
    """Keeps only the most recent user/assistant turns, dropping older ones.

    A "turn" here is one message; callers that already summarize older
    history (see Phase 5's rolling conversation summary) should prepend
    that summary as a single system message before calling this.
    """
    if max_turns <= 0:
        return []
    return turns[-max_turns:]
