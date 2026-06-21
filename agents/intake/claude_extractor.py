from __future__ import annotations

import json
import os
from typing import Any

from pydantic import ValidationError

from .errors import ClaudeExtractionError, MissingAnthropicAPIKeyError
from .schemas import IntakeExtraction

try:
    from dotenv import find_dotenv, load_dotenv
except ImportError:  # pragma: no cover - python-dotenv is listed in requirements.
    find_dotenv = None
    load_dotenv = None


CLAUDE_MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """
You are the Intake Agent for a clinic voicemail triage system.
Extract only facts that are explicitly present in the speech-to-text transcript.
Do not infer patient identity, insurance, dates, phone numbers, or request details.
If a field is not stated, return null for scalar fields or [] for arrays.

Return JSON only with exactly these keys:
first_name, last_name, date_of_birth, phone_number, insurance_plan, request, missing_fields.

Rules:
- date_of_birth must be YYYY-MM-DD if the transcript gives enough information; otherwise null.
- phone_number should preserve the stated callback number as digits or a readable phone string.
- request must be an object with exactly these keys: type, details, orders, preferred_times, urgency_signal.
- request.type must be one of: refill, reschedule, message_relay, unknown.
- request.details should be a concise factual summary of what the caller requested.
- request.orders should list requested medications/orders/items explicitly named by the caller, such as ["Lisinopril 10 mg once daily with food"]. Use [] when none are stated.
- request.preferred_times is an array of appointment time preferences stated by the caller.
- request.urgency_signal must be one of: routine, urgent, emergency, unknown.
- missing_fields should include any missing required intake fields from:
  first_name, last_name, date_of_birth, phone_number, request.details, insurance_plan.
""".strip()


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


def extract_intake_fields_with_claude(
    *,
    transcript: str,
    stt_json: dict[str, Any],
    api_key: str | None = None,
    client: Any | None = None,
) -> IntakeExtraction:
    resolved_key = get_anthropic_api_key(api_key)

    if client is None:
        import anthropic

        client = anthropic.Anthropic(api_key=resolved_key)

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=800,
        temperature=0,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "transcript": transcript,
                        "stt_json": stt_json,
                    }
                ),
            }
        ],
    )
    raw_text = _text_from_message(message)
    parsed = _parse_json_only(raw_text)

    try:
        extraction = IntakeExtraction(**parsed, transcript=transcript)
    except ValidationError as exc:
        raise ClaudeExtractionError() from exc

    return extraction


def _text_from_message(message: Any) -> str:
    return "".join(
        block.text for block in message.content if getattr(block, "type", None) == "text"
    ).strip()


def _parse_json_only(raw_text: str) -> dict[str, Any]:
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ClaudeExtractionError() from exc

    if not isinstance(payload, dict):
        raise ClaudeExtractionError()
    return payload
