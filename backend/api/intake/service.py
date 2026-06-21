from __future__ import annotations

import logging
from typing import Any, Callable

from transcription.schemas import TranscriptionResponse, to_plain_dict
from transcription.service import transcribe_audio

from tasks.repo import TasksRepo

from .claude_extractor import extract_intake_fields_with_claude
from .orchestrator import route_intake_to_orchestrator
from .schemas import IntakeExtraction
from .stt import extract_transcript_from_stt_json

logger = logging.getLogger("intake")


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
    voicemail_id = _persist_voicemail(transcription.transcript)
    orchestrator_results = await route_intake_to_orchestrator(
        intake, task_id=task_id, voicemail_id=voicemail_id
    )
    return transcription, intake, orchestrator_results


def _persist_voicemail(transcript: str) -> str | None:
    """Store the transcript as a voicemails row so dashboard tasks can link to
    it. Best-effort: a Supabase failure must not break intake processing."""
    try:
        row = TasksRepo().insert_voicemail({"transcript": transcript})
    except Exception:  # noqa: BLE001 - persistence is best-effort here.
        logger.exception("Failed to persist voicemail transcript")
        return None
    return row.get("id")
