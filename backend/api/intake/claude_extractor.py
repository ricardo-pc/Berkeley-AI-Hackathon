from __future__ import annotations

import json
import os
from datetime import date, datetime
from typing import Any

from pydantic import ValidationError

from .errors import ClaudeExtractionError, MissingAnthropicAPIKeyError
from .schemas import IntakeExtraction

try:
    from dotenv import find_dotenv, load_dotenv
except ImportError:  # pragma: no cover - python-dotenv is listed in requirements.
    find_dotenv = None
    load_dotenv = None


CLAUDE_MODEL = "claude-haiku-4-5"

SYSTEM_PROMPT = """
You are the Intake Agent for a clinic voicemail triage system.
Extract only facts that are explicitly present in the speech-to-text transcript.
Do not infer patient identity, insurance, dates, phone numbers, or request details.
If a field is not stated, return null for scalar fields or [] for arrays.

Return JSON only with exactly these keys:
first_name, last_name, date_of_birth, phone_number, insurance_plan, request, requests, missing_fields.

Rules:
- date_of_birth must be YYYY-MM-DD if the transcript gives enough information; otherwise null.
- phone_number should preserve the stated callback number as digits or a readable phone string.
- request must be an object with exactly these keys: type, details, orders, preferred_times, urgency_signal.
- requests must be an array of request objects with the same keys as request.
- request is the primary or first request; requests contains every distinct request in the voicemail.
- If the caller makes exactly one request, requests must contain one object identical to request.
- If the caller makes multiple requests, such as a refill plus a doctor message, create one request object per workflow item and put them all in requests in the order the caller stated them.
- request.type must be one of: refill, reschedule, message_relay, unknown.
- request.type is the workflow category, not the medical urgency. Never return emergency as request.type.
- Use request.type message_relay when the caller asks the clinic to notify, tell, message, or relay information to a doctor/provider, including medication side effects or symptoms.
- Use request.type unknown for acute symptoms or safety concerns that do not include a refill, reschedule, or relay-to-provider request.
- request.details should be a concise factual summary of what the caller requested.
- request.orders should list only medications/orders/items the caller is explicitly asking the clinic to refill, order, schedule, or otherwise act on, such as ["Lisinopril"]. Use [] when none are requested.
- Do not include medications that are only mentioned as context, history, current medications, side effects, or symptoms. For example, "I feel dizzy since starting Sertraline" is a message relay with orders [].
- Do not include dosages in request.orders.
- request.preferred_times must be an array of objects, never plain strings.
- Each preferred_times object must have exactly these keys: raw_text, date, start_time, time_of_day.
- raw_text is the caller's original time phrase, such as "June 24th at 3 PM".
- The user message includes reference_date (the date the voicemail was received, YYYY-MM-DD) and reference_weekday (its day of the week). Treat reference_date as "today" and use it to resolve every relative or partial date phrase into a concrete date.
- date must be a concrete YYYY-MM-DD calendar date. Resolve it whenever the caller names a specific day, even relatively; only use null when the caller gives no day at all, such as "sometime next week" or a bare "in the morning".
- Resolve relative phrases against reference_date: "today" is reference_date, "tomorrow" is reference_date plus one day, and a weekday name such as "Tuesday", "this Tuesday", or "next Tuesday" is the soonest date strictly after reference_date that falls on that weekday. The resolved date's weekday must match the weekday the caller named.
- If the caller states a month and day with no year, such as "June 24th", choose the year that makes the date fall on or after reference_date.
- start_time must be a 24-hour HH:MM string when a specific time is stated; otherwise null.
- time_of_day must be one of: morning, afternoon, evening, anytime, unknown.
- Example (reference_date 2026-06-20): "June 24th at 3 PM" should become {"raw_text":"June 24th at 3 PM","date":"2026-06-24","start_time":"15:00","time_of_day":"afternoon"}.
- Example (reference_date 2026-06-20, a Saturday): "next Tuesday morning" should become {"raw_text":"next Tuesday morning","date":"2026-06-23","start_time":null,"time_of_day":"morning"}.
- request.urgency_signal must be one of: routine, urgent, emergency, unknown. Put clinical urgency here, not in request.type.
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
    reference_date: date | None = None,
) -> IntakeExtraction:
    resolved_key = get_anthropic_api_key(api_key)

    if client is None:
        import anthropic

        client = anthropic.Anthropic(api_key=resolved_key)

    resolved_reference_date = _resolve_reference_date(stt_json, reference_date)

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
                        "reference_date": resolved_reference_date.isoformat(),
                        "reference_weekday": resolved_reference_date.strftime("%A"),
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


def _resolve_reference_date(
    stt_json: dict[str, Any], reference_date: date | None
) -> date:
    """Date to treat as "today" when resolving relative time phrases.

    Prefers an explicit override, then the voicemail's recorded timestamp from
    the STT payload, and finally falls back to the current date.
    """
    if reference_date is not None:
        return reference_date

    created = (
        ((stt_json.get("raw_provider_response") or {}).get("metadata") or {}).get("created")
    )
    if isinstance(created, str) and created.strip():
        try:
            return datetime.fromisoformat(created.replace("Z", "+00:00")).date()
        except ValueError:
            pass

    return date.today()


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
