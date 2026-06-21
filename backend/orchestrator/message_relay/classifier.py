from __future__ import annotations

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
    "You triage a voicemail message a patient left for a primary-care clinic and decide how it "
    "should be handled. Choose exactly one route:\n"
    "- \"physician\": a clinical concern that the doctor must see — a negative change in the "
    "patient's status, an adverse or unreasonable reaction to a medication, or any reported "
    "discomfort, pain, or symptom.\n"
    "- \"staff\": an actionable request a non-physician healthcare worker can handle without the "
    "doctor — a work/school excuse or accommodation, requesting medication samples, or a simple "
    "non-clinical question.\n"
    "- \"none\": not worth relaying — thanks, confirmations, spam, or anything needing no action.\n"
    "If the route is physician or staff, write draft_message: a concise, factual one- or two-"
    "sentence message the clinic can forward to the recipient. In draft_message include ONLY "
    "facts the patient actually stated — do not add reasons, causes, diagnoses, or details they "
    "did not give (for example, if the patient says nothing is wrong, do not write 'due to "
    "illness'). If the patient names a specific doctor, capture it in mentioned_doctor. The "
    "reasoning field is your private note to the reviewing healthcare worker and may include "
    "clinical interpretation; keep it brief and always provide it."
)

DECISION_TOOL = {
    "name": "record_relay_decision",
    "description": "Record the triage decision for the patient's message.",
    "input_schema": {
        "type": "object",
        "properties": {
            "route": {
                "type": "string",
                "enum": ["physician", "staff", "none"],
                "description": "Who should handle this message.",
            },
            "category": {
                "type": "string",
                "description": "Short snake_case label, e.g. adverse_medication_reaction, "
                "work_accommodation, sample_request, simple_question, not_actionable.",
            },
            "draft_message": {
                "type": "string",
                "description": "Concise message to forward. Empty string if route is none.",
            },
            "mentioned_doctor": {
                "type": "string",
                "description": "Doctor named in the message, or empty string if none named.",
            },
            "reasoning": {
                "type": "string",
                "description": "Brief reason for the routing decision (always provided).",
            },
        },
        "required": ["route", "category", "reasoning"],
    },
}


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


def classify_message(
    message: str,
    *,
    api_key: str | None = None,
    client: Any | None = None,
) -> dict[str, Any]:
    """Return the structured routing decision for a patient message."""
    resolved_key = get_anthropic_api_key(api_key)

    if client is None:
        import anthropic

        client = anthropic.Anthropic(api_key=resolved_key)

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=400,
        system=SYSTEM_PROMPT,
        tools=[DECISION_TOOL],
        tool_choice={"type": "tool", "name": "record_relay_decision"},
        messages=[{"role": "user", "content": message}],
    )

    for block in response.content:
        if getattr(block, "type", None) == "tool_use":
            return dict(block.input)

    # Tool use was forced, so this should not happen; fail safe to "none".
    return {
        "route": "none",
        "category": "not_actionable",
        "reasoning": "Could not classify the message.",
    }
