from __future__ import annotations

from typing import Any, Callable

from .claude_extractor import extract_intake_fields_with_claude
from .schemas import IntakeExtraction
from .stt import extract_transcript_from_stt_json


def run_intake_extraction(
    stt_json: dict[str, Any],
    *,
    extract: Callable[..., IntakeExtraction] = extract_intake_fields_with_claude,
) -> IntakeExtraction:
    transcript = extract_transcript_from_stt_json(stt_json)
    return extract(transcript=transcript, stt_json=stt_json)

