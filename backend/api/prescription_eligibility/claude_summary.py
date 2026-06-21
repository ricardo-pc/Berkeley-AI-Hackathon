from __future__ import annotations

import json
import os
from typing import Any

from .errors import MissingAnthropicAPIKeyError

try:
    from dotenv import find_dotenv, load_dotenv
except ImportError:  # pragma: no cover - python-dotenv is listed in requirements.
    find_dotenv = None
    load_dotenv = None


CLAUDE_MODEL = "claude-haiku-4-5-20251001"

SYSTEM_PROMPT = (
    "You write a one-paragraph plain-English summary for a certified healthcare worker (CHW) "
    "reviewing a patient's prescription refill request. State clearly whether it can proceed, "
    "which requirement (if any) is unmet, and call out any drug-interaction warning so a "
    "physician notices it even if the refill is otherwise approved. Be concise and factual — "
    "do not invent any information beyond what is given."
)


def load_environment() -> None:
    if not find_dotenv or not load_dotenv:
        return
    env_path = find_dotenv(usecwd=True)
    if env_path:
        load_dotenv(env_path)


def get_anthropic_api_key(api_key: str | None = None) -> str:
    load_environment()
    resolved = api_key if api_key is not None else os.getenv("ANTHROPIC_API_KEY")
    if not resolved:
        raise MissingAnthropicAPIKeyError()
    return resolved


def generate_agent_summary(
    checks: dict[str, Any],
    *,
    api_key: str | None = None,
    client: Any | None = None,
) -> str:
    resolved_key = get_anthropic_api_key(api_key)

    if client is None:
        import anthropic

        client = anthropic.Anthropic(api_key=resolved_key)

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=200,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": json.dumps(checks)}],
    )
    return "".join(
        block.text for block in message.content if getattr(block, "type", None) == "text"
    ).strip()
