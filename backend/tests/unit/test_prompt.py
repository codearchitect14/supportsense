from app.services.llm.base import LLMMessage
from app.services.llm.prompt import build_system_prompt, trim_history


def test_build_system_prompt_caps_to_max_snippets():
    snippets = ["one", "two", "three", "four"]
    prompt = build_system_prompt(snippets, max_snippets=2)
    assert prompt.count("[") == 2
    assert "three" not in prompt
    assert "four" not in prompt


def test_build_system_prompt_falls_back_with_no_snippets():
    prompt = build_system_prompt([])
    assert "not sure" in prompt.lower() or "escalate" in prompt.lower()


def test_trim_history_keeps_only_last_n_turns():
    history = [LLMMessage(role="user", content=str(i)) for i in range(10)]
    trimmed = trim_history(history, max_turns=4)
    assert [m.content for m in trimmed] == ["6", "7", "8", "9"]


def test_trim_history_zero_turns_returns_empty():
    history = [LLMMessage(role="user", content="hi")]
    assert trim_history(history, max_turns=0) == []


def test_trim_history_fewer_turns_than_max_returns_all():
    history = [LLMMessage(role="user", content="hi")]
    assert trim_history(history, max_turns=4) == history
