"""A deliberately simple example guard. Replace the body of `blocked` with your own filter.
Contract: take the prompt text, return True if you would BLOCK it, False if you would allow it.
If your guard cannot decide (for example a model or network call fails), RAISE an exception: no verdict is never counted as a pass."""
import re

_PATTERNS = [
    r"ignore (all )?(the )?(previous|prior|above|earlier) (instructions|rules)",
    r"(reveal|show|print|repeat).{0,30}(system prompt|hidden (rules|instructions))",
    r"developer mode",
]


def blocked(text: str) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in _PATTERNS)
