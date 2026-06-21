from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

API_ROOT = Path(__file__).resolve().parent
ORCHESTRATOR_ROOT = API_ROOT.parent / "orchestrator"
sys.path.insert(0, str(ORCHESTRATOR_ROOT))

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from confirmation.errors import ConfirmationError
from confirmation.service import send_confirmation
from intake.errors import IntakeAgentError
from intake.errors import error_payload as intake_error_payload
from intake.orchestrator import route_workflow_payload_to_orchestrator
from intake.schemas import IntakeExtraction, to_plain_dict as intake_to_plain_dict
from intake.service import run_intake_extraction, run_voicemail_intake_workflow
from prescription_fulfillment.errors import PrescriptionFulfillmentError
from prescription_fulfillment.errors import error_payload as fulfillment_error_payload
from prescription_fulfillment.repo import SupabasePrescriptionFulfillmentRepo
from prescription_fulfillment.schemas import RefillRequest
from prescription_fulfillment.service import fill_prescription
from scheduler.errors import SchedulerError
from scheduler.errors import error_payload as scheduler_error_payload
from scheduler.repo import SupabaseSchedulerRepo
from scheduler.schemas import BookingRequest
from scheduler.service import book_appointment
from summary.claude_summary import generate_narrative
from summary.errors import SummaryError
from summary.errors import error_payload as summary_error_payload
from summary.repo import SupabaseSummaryRepo
from summary.service import build_daily_digest
from transcription.errors import InvalidAudioError, TranscriptionError, error_payload
from transcription.schemas import TranscriptionResponse, to_plain_dict
from transcription.service import normalize_deepgram_response, transcribe_audio


JAMES_MOCK_TRANSCRIPTION_PATH = API_ROOT / "contracts" / "james_mock_transcription.json"


class IntakeAPIRequest(BaseModel):
    stt_json: dict[str, Any]


class IntakeWorkflowRequest(BaseModel):
    intake: IntakeExtraction
    provider_id: str | None = None
    requested_start: datetime | None = None
    requested_end: datetime | None = None
    cancel_appointment_id: str | None = None
    task_id: str | None = None


app = FastAPI(
    title="Clinic Voicemail Speech-to-Text API",
    version="0.1.0",
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/intake")
async def create_intake(payload: IntakeAPIRequest):
    try:
        intake = run_intake_extraction(payload.stt_json)
    except IntakeAgentError as exc:
        return _intake_error_response(exc)

    return _sanitize_intake(intake)


@app.post("/api/voicemail/intake")
async def create_voicemail_intake(file: UploadFile | None = File(default=None)):
    if file is None:
        return _error_response(InvalidAudioError())

    try:
        audio_bytes = await file.read()
        transcription, intake, orchestrator_results = await run_voicemail_intake_workflow(
            audio_bytes,
            filename=file.filename,
            content_type=file.content_type,
        )
    except TranscriptionError as exc:
        return _error_response(exc)
    except IntakeAgentError as exc:
        return _intake_error_response(exc)

    return {
        "transcript": _compact_transcript(transcription.transcript),
        "intake": _sanitize_intake(intake),
        "orchestrator_results": orchestrator_results,
    }


@app.post("/api/transcriptions", response_model=TranscriptionResponse)
async def create_transcription(file: UploadFile | None = File(default=None)):
    if file is None:
        return _error_response(InvalidAudioError())

    try:
        audio_bytes = await file.read()
        result = await transcribe_audio(
            audio_bytes,
            filename=file.filename,
            content_type=file.content_type,
        )
    except TranscriptionError as exc:
        return _error_response(exc)

    return to_plain_dict(result)


@app.post("/api/transcriptions/text")
async def create_transcription_text(file: UploadFile | None = File(default=None)):
    if file is None:
        return _error_response(InvalidAudioError())

    try:
        audio_bytes = await file.read()
        result = await transcribe_audio(
            audio_bytes,
            filename=file.filename,
            content_type=file.content_type,
        )
    except TranscriptionError as exc:
        return _error_response(exc)

    return {"transcript": _compact_transcript(result.transcript)}


@app.get("/api/mock/transcriptions/james", response_model=TranscriptionResponse)
async def mock_james_transcription():
    return to_plain_dict(_load_james_mock_transcription())


@app.get("/api/mock/transcriptions/james/text")
async def mock_james_transcription_text():
    result = _load_james_mock_transcription()
    return {"transcript": _compact_transcript(result.transcript)}


def _error_response(exc: TranscriptionError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=error_payload(exc))


def _intake_error_response(exc: IntakeAgentError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=intake_error_payload(exc))


def _compact_transcript(transcript: str) -> str:
    return re.sub(r"\s+", " ", transcript).strip()


def _sanitize_intake(intake: IntakeExtraction) -> dict[str, Any]:
    payload = intake_to_plain_dict(intake)
    payload["transcript"] = _compact_transcript(payload.get("transcript") or "")
    return payload


def _load_james_mock_transcription() -> TranscriptionResponse:
    raw = json.loads(JAMES_MOCK_TRANSCRIPTION_PATH.read_text(encoding="utf-8"))
    return normalize_deepgram_response(raw)


@app.post("/api/schedule-eligibility")
async def create_schedule_eligibility_check(payload: IntakeWorkflowRequest):
    return await route_workflow_payload_to_orchestrator(
        payload.intake,
        path="/api/reschedule",
        task_id=payload.task_id,
    )


@app.post("/api/prescription-eligibility")
async def create_prescription_eligibility_check(payload: IntakeWorkflowRequest):
    return await route_workflow_payload_to_orchestrator(
        payload.intake,
        path="/api/refill",
        task_id=payload.task_id,
    )


@app.post("/api/appointments")
async def create_appointment(payload: BookingRequest):
    try:
        repo = SupabaseSchedulerRepo()
        result = book_appointment(
            patient_id=payload.patient_id,
            first_name=payload.first_name,
            last_name=payload.last_name,
            dob=payload.dob,
            provider_id=payload.provider_id,
            start_time=payload.start_time,
            end_time=payload.end_time,
            cancel_appointment_id=payload.cancel_appointment_id,
            visit_type=payload.visit_type,
            task_id=payload.task_id,
            repo=repo,
        )
    except SchedulerError as exc:
        return JSONResponse(status_code=exc.status_code, content=scheduler_error_payload(exc))

    result["confirmation"] = _try_send_confirmation("reschedule", result)
    return result


@app.post("/api/prescriptions")
async def create_prescription_refill(payload: RefillRequest):
    try:
        repo = SupabasePrescriptionFulfillmentRepo()
        result = fill_prescription(
            patient_id=payload.patient_id,
            first_name=payload.first_name,
            last_name=payload.last_name,
            dob=payload.dob,
            medication_name=payload.medication_name,
            dosage=payload.dosage,
            instructions=payload.instructions,
            provider_id=payload.provider_id,
            task_id=payload.task_id,
            repo=repo,
        )
    except PrescriptionFulfillmentError as exc:
        return JSONResponse(status_code=exc.status_code, content=fulfillment_error_payload(exc))

    result["confirmation"] = _try_send_confirmation("prescription_refill", result)
    return result


def _try_send_confirmation(task_type: str, result: dict) -> dict | None:
    """Best-effort: a confirmation text failing to send must not undo an already-successful booking/refill."""
    phone_number = (result.get("patient") or {}).get("phone")
    if not phone_number:
        return {"sent": False, "reason": "no phone number on file"}

    try:
        sent = send_confirmation(task_type=task_type, phone_number=phone_number, result=result)
    except ConfirmationError as exc:
        return {"sent": False, "reason": str(exc)}

    return {"sent": sent is not None, **(sent or {})}


@app.post("/api/message-relay")
async def create_message_relay_check(payload: IntakeWorkflowRequest):
    return await route_workflow_payload_to_orchestrator(
        payload.intake,
        path="/api/message-relay",
        task_id=payload.task_id,
    )


@app.get("/api/summary")
async def get_daily_digest(since: datetime | None = None):
    try:
        repo = SupabaseSummaryRepo()
        result = build_daily_digest(since=since, repo=repo, summarize=generate_narrative)
    except SummaryError as exc:
        return JSONResponse(status_code=exc.status_code, content=summary_error_payload(exc))

    return result
