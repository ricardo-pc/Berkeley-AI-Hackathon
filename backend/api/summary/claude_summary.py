from __future__ import annotations

import json
import os
from typing import Any

try:
    from dotenv import find_dotenv, load_dotenv
except ImportError:  # pragma: no cover - python-dotenv is listed in requirements.
    find_dotenv = None
    load_dotenv = None


CLAUDE_MODEL = "claude-haiku-4-5-20251001"

SYSTEM_PROMPT = (
    "You write a short end-of-day digest paragraph for hospital front-desk staff, "
    "summarizing the structured task counts and lists you're given: what was "
    "completed, what's flagged for manual review, what's still pending approval, "
    "and which patients have insurance issues on file. Be concise and factual -- "
    "do not invent any information beyond what is given."
)


def load_environment() -> None:
    if not find_dotenv or not load_dotenv:
        return
    env_path = find_dotenv(usecwd=True)
    if env_path:
        load_dotenv(env_path)


def generate_narrative(
    digest: dict[str, Any],
    *,
    api_key: str | None = None,
    client: Any | None = None,
) -> str | None:
    """Best-effort: returns None instead of raising if Claude isn't configured.

    The digest is still fully useful without this -- it's a narrative layer on
    top of structured data that's already correct on its own.
    """
    load_environment()
    resolved_key = api_key if api_key is not None else os.getenv("ANTHROPIC_API_KEY")
    if not resolved_key:
        return None

    if client is None:
        import anthropic

        client = anthropic.Anthropic(api_key=resolved_key)

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=200,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": json.dumps(digest)}],
    )
    return "".join(
        block.text for block in message.content if getattr(block, "type", None) == "text"
    ).strip()
