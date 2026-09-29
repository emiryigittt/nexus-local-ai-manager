"""Bounded recent conversation context shared by the API and desktop client."""

from collections.abc import Iterable

MAX_CONTEXT_CHARS = 16_000
MAX_CONTEXT_MESSAGES = 24


def recent_turns(messages: Iterable[dict]) -> list[dict[str, str]]:
    """Keep complete user/assistant turns; omit failed attempts and other roles."""
    pairs = []
    pending = None
    for message in messages:
        role, content = message.get("role"), message.get("content")
        if not isinstance(content, str) or not content.strip():
            continue
        if role == "user":
            pending = {"role": "user", "content": content}
        elif role == "assistant" and pending:
            pairs.append([pending, {"role": "assistant", "content": content}])
            pending = None
    selected = []
    size = 0
    for pair in reversed(pairs[-MAX_CONTEXT_MESSAGES // 2:]):
        cost = sum(len(message["content"]) for message in pair)
        if size + cost > MAX_CONTEXT_CHARS:
            break
        selected.append(pair)
        size += cost
    return [message for pair in reversed(selected) for message in pair]
