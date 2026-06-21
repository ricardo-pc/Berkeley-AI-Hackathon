from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from agents.intake.claude_extractor import extract_intake_fields_with_claude
from agents.intake.errors import (
    ClaudeExtractionError,
    InvalidSTTPayloadError,
    MissingAnthropicAPIKeyError,
)
from agents.intake.schemas import IntakeExtraction, to_plain_dict
from agents.intake.service import run_intake_extraction
from agents.intake.stt import extract_transcript_from_stt_json


ROOT = Path(__file__).resolve().parents[1]
DEEPGRAM_FIXTURE = ROOT / "tests" / "fixtures" / "deepgram_pre_recorded_success.json"
CLAUDE_FIXTURE = ROOT / "tests" / "fixtures" / "intake_claude_success.json"


class FakeTextBlock:
    type = "text"

    def __init__(self, text: str):
        self.text = text


class FakeMessage:
    def __init__(self, text: str):
        self.content = [FakeTextBlock(text)]


class FakeMessagesAPI:
    def __init__(self, text: str):
        self._text = text
        self.last_call: dict[str, Any] | None = None

    def create(self, **kwargs):
        self.last_call = kwargs
        return FakeMessage(self._text)


class FakeAnthropicClient:
    def __init__(self, text: str):
        self.messages = FakeMessagesAPI(text)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_extract_transcript_from_normalized_stt_json():
    stt_json = {
        "transcript": "Hello, this is Maria Gonzalez calling about my prescription."
    }

    transcript = extract_transcript_from_stt_json(stt_json)

    assert transcript == "Hello, this is Maria Gonzalez calling about my prescription."


def test_extract_transcript_from_raw_deepgram_json():
    stt_json = load_json(DEEPGRAM_FIXTURE)

    transcript = extract_transcript_from_stt_json(stt_json)

    assert transcript == "Hi, this is Maria Garcia. I need to refill my blood pressure medication."


def test_missing_transcript_raises_stable_error():
    with pytest.raises(InvalidSTTPayloadError) as exc_info:
        extract_transcript_from_stt_json({"results": {"channels": []}})

    assert exc_info.value.code == "invalid_stt_payload"
    assert exc_info.value.status_code == 400


def test_missing_anthropic_key_raises_stable_error():
    with pytest.raises(MissingAnthropicAPIKeyError) as exc_info:
        extract_intake_fields_with_claude(transcript="hello", stt_json={}, api_key="")

    assert exc_info.value.code == "missing_anthropic_api_key"
    assert exc_info.value.status_code == 500


def test_claude_extraction_returns_strict_intake_schema():
    claude_payload = load_json(CLAUDE_FIXTURE)
    client = FakeAnthropicClient(json.dumps(claude_payload))

    result = extract_intake_fields_with_claude(
        transcript="Maria Gonzalez, born March 12 1978, needs a refill.",
        stt_json={"transcript": "Maria Gonzalez, born March 12 1978, needs a refill."},
        api_key="test-key",
        client=client,
    )

    assert isinstance(result, IntakeExtraction)
    assert to_plain_dict(result) == {
        **claude_payload,
        "transcript": "Maria Gonzalez, born March 12 1978, needs a refill.",
    }
    assert client.messages.last_call["model"]
    assert client.messages.last_call["temperature"] == 0
    assert "stt_json" in client.messages.last_call["messages"][0]["content"]


def test_claude_extraction_rejects_non_json():
    client = FakeAnthropicClient("first name is Maria")

    with pytest.raises(ClaudeExtractionError) as exc_info:
        extract_intake_fields_with_claude(
            transcript="Maria needs a refill.",
            stt_json={"transcript": "Maria needs a refill."},
            api_key="test-key",
            client=client,
        )

    assert exc_info.value.code == "claude_extraction_error"
    assert exc_info.value.status_code == 502


def test_service_passes_transcript_and_stt_json_to_extractor():
    stt_json = {"transcript": "Robert Martinez wants to move his appointment to Friday afternoon."}
    seen: dict[str, Any] = {}

    def fake_extract(*, transcript: str, stt_json: dict[str, Any]) -> IntakeExtraction:
        seen["transcript"] = transcript
        seen["stt_json"] = stt_json
        return IntakeExtraction(
            first_name="Robert",
            last_name="Martinez",
            request={
                "type": "reschedule",
                "details": "Patient wants to move his appointment to Friday afternoon.",
                "preferred_times": ["Friday afternoon"],
                "urgency_signal": "routine",
            },
            transcript=transcript,
        )

    result = run_intake_extraction(stt_json, extract=fake_extract)

    assert seen == {
        "transcript": "Robert Martinez wants to move his appointment to Friday afternoon.",
        "stt_json": stt_json,
    }
    assert result.request.type == "reschedule"
    assert result.request.preferred_times == ["Friday afternoon"]
