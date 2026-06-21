from __future__ import annotations

from typing import Any, Callable

from transcription.schemas import TranscriptionResponse, to_plain_dict
from transcription.service import transcribe_audio

from .claude_extractor import extract_intake_fields_with_claude
from .orchestrator import route_intake_to_orchestrator
from .schemas import IntakeExtraction
from .stt import extract_transcript_from_stt_json


def run_intake_extraction(
    stt_json: dict[str, Any],
    *,
    extract: Callable[..., IntakeExtraction] = extract_intake_fields_with_claude,
) -> IntakeExtraction:
    transcript = extract_transcript_from_stt_json(stt_json)
    return extract(transcript=transcript, stt_json=stt_json)


async def run_voicemail_intake_workflow(
    audio_bytes: bytes,
    *,
    filename: str | None,
    content_type: str | None = None,
    task_id: str | None = None,
) -> tuple[TranscriptionResponse, IntakeExtraction, list[dict[str, Any]]]:
    transcription = await transcribe_audio(
        audio_bytes,
        filename=filename,
        content_type=content_type,
    )
    intake = run_intake_extraction(to_plain_dict(transcription))
    orchestrator_results = await route_intake_to_orchestrator(intake, task_id=task_id)
    return transcription, intake, orchestrator_results
