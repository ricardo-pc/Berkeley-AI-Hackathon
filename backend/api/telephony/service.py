from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from intake.schemas import to_plain_dict as intake_to_dict
from intake.service import run_intake_extraction
from transcription.schemas import to_plain_dict as transcription_to_dict
from transcription.service import transcribe_audio

from .config import TelephonyConfig, get_telephony_config
from .recordings import download_recording

logger = logging.getLogger("telephony")

API_ROOT = Path(__file__).resolve().parents[1]  # backend/api


def _output_dir() -> Path:
    import os

    configured = os.getenv("VOICEMAIL_OUTPUT_DIR")
    directory = Path(configured) if configured else API_ROOT / "telephony_output"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _run_intake(stt_json: dict[str, Any]) -> dict[str, Any]:
    return intake_to_dict(run_intake_extraction(stt_json))


async def process_voicemail_recording(
    *,
    recording_url: str,
    call_sid: str | None = None,
    recording_sid: str | None = None,
    from_number: str | None = None,
    config: TelephonyConfig | None = None,
) -> dict[str, Any]:
    """Download a provider voicemail, transcribe it, and run the intake agent.

    Returns the persisted record. Designed to run inside a background task, so
    it logs and re-raises rather than assuming a caller is waiting.
    """
    config = config or get_telephony_config()
    key = recording_sid or call_sid or uuid4().hex
    logger.info("Processing voicemail recording %s (call %s)", key, call_sid)

    audio_bytes, content_type, filename = await download_recording(recording_url, config)
    transcription = await transcribe_audio(
        audio_bytes, filename=filename, content_type=content_type
    )
    stt_json = transcription_to_dict(transcription)

    transcript = str(stt_json.get("transcript") or "").strip()
    if transcript:
        intake_json = _run_intake(stt_json)
        status = "processed"
    else:
        intake_json = _skipped_intake_payload("no_transcript")
        status = "intake_skipped_no_transcript"
        logger.info("Skipping intake for %s because Deepgram returned no transcript", key)

    record = {
        "call_sid": call_sid,
        "recording_sid": recording_sid,
        "from_number": from_number,
        "telephony_provider": config.provider,
        "received_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "transcript": transcript,
        "intake": intake_json,
    }
    _persist(key, stt_json=stt_json, intake_json=intake_json, record=record)
    logger.info("Stored voicemail intake for %s", key)
    return record


async def process_voicemail_recording_safe(**kwargs: Any) -> None:
    """Background-task wrapper that never lets an exception escape unlogged."""
    try:
        await process_voicemail_recording(**kwargs)
    except Exception:  # noqa: BLE001 - background task: log and swallow.
        logger.exception("Failed to process voicemail recording")


def _persist(
    key: str,
    *,
    stt_json: dict[str, Any],
    intake_json: dict[str, Any],
    record: dict[str, Any],
) -> None:
    directory = _output_dir()
    safe_key = _safe_filename(key)
    (directory / f"{safe_key}.stt.json").write_text(
        json.dumps(stt_json, indent=2), encoding="utf-8"
    )
    (directory / f"{safe_key}.intake.json").write_text(
        json.dumps(intake_json, indent=2), encoding="utf-8"
    )
    (directory / f"{safe_key}.voicemail.json").write_text(
        json.dumps(record, indent=2), encoding="utf-8"
    )


def _skipped_intake_payload(reason: str) -> dict[str, Any]:
    messages = {
        "no_transcript": "Recording did not contain a usable speech transcript.",
    }
    return {
        "status": "skipped",
        "reason": reason,
        "message": messages.get(reason, "Intake was skipped."),
    }


def _safe_filename(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in value)
