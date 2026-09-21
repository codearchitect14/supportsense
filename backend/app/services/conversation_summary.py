SUMMARY_ROLE = "summary"
_MAX_LINE_CHARS = 160


def summarize_turns(turns: list[tuple[str, str]]) -> str:
    """Builds a compact rolling summary from (role, content) turns.

    This is a cheap, local heuristic (truncate each turn to one line and
    concatenate), not an LLM call, so rolling a conversation's older history
    into a summary never itself costs a token-minimization budget.
    """
    lines = []
    for role, content in turns:
        flat = " ".join(content.split())
        if len(flat) > _MAX_LINE_CHARS:
            flat = flat[: _MAX_LINE_CHARS - 1] + "…"
        lines.append(f"{role}: {flat}")
    return "Earlier in this conversation:\n" + "\n".join(lines)
