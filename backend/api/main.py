from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from confirmation.errors import ConfirmationError
from confirmation.service import send_confirmation
from intake.errors import IntakeAgentError
from intake.errors import error_payload as intake_error_payload
from intake.schemas import IntakeExtraction, to_plain_dict as intake_to_plain_dict
from intake.service import run_intake_extraction
from message_relay.errors import MessageRelayError
from message_relay.errors import error_payload as message_relay_error_payload
from message_relay.repo import SupabaseMessageRelayRepo
from message_relay.service import run_message_relay_check
from prescription_eligibility.errors import PrescriptionEligibilityError
from prescription_eligibility.errors import error_payload as prescription_error_payload
from prescription_eligibility.repo import SupabasePrescriptionEligibilityRepo
from prescription_eligibility.service import run_prescription_eligibility_check
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
from scheduling_eligibility.errors import ScheduleEligibilityError
from scheduling_eligibility.errors import error_payload as schedule_error_payload
from scheduling_eligibility.repo import SupabaseScheduleEligibilityRepo
from scheduling_eligibility.schemas import ScheduleEligibilityRequest
from scheduling_eligibility.service import run_schedule_eligibility_check
from transcription.errors import InvalidAudioError, TranscriptionError, error_payload
from transcription.schemas import TranscriptionResponse, to_plain_dict
from transcription.service import normalize_deepgram_response, transcribe_audio


API_ROOT = Path(__file__).resolve().parent
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
        transcription = await transcribe_audio(
            audio_bytes,
            filename=file.filename,
            content_type=file.content_type,
        )
        stt_json = to_plain_dict(transcription)
        intake = run_intake_extraction(stt_json)
    except TranscriptionError as exc:
        return _error_response(exc)
    except IntakeAgentError as exc:
        return _intake_error_response(exc)

    return {
        "transcript": _compact_transcript(transcription.transcript),
        "intake": _sanitize_intake(intake),
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


def _api_error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": {"code": code, "message": message}})


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
    if _normalize_intake_request_type(payload.intake.request.type) != "reschedule":
        return _api_error_response(
            400,
            "wrong_request_type",
            "Schedule eligibility requires intake.request.type to be reschedule.",
        )
    if not payload.provider_id or not payload.requested_start or not payload.requested_end:
        return _api_error_response(
            400,
            "missing_schedule_fields",
            "provider_id, requested_start, and requested_end are required for schedule eligibility.",
        )
    patient_or_error = _resolve_patient_from_intake(payload.intake)
    if isinstance(patient_or_error, JSONResponse):
        return patient_or_error

    try:
        repo = SupabaseScheduleEligibilityRepo()
        result = run_schedule_eligibility_check(
            patient_id=patient_or_error["id"],
            provider_id=payload.provider_id,
            requested_start=payload.requested_start,
            requested_end=payload.requested_end,
            cancel_appointment_id=payload.cancel_appointment_id,
            task_id=payload.task_id,
            repo=repo,
        )
    except ScheduleEligibilityError as exc:
        return _schedule_eligibility_error_response(exc)

    return result


def _schedule_eligibility_error_response(exc: ScheduleEligibilityError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=schedule_error_payload(exc))


@app.post("/api/prescription-eligibility")
async def create_prescription_eligibility_check(payload: IntakeWorkflowRequest):
    if _normalize_intake_request_type(payload.intake.request.type) != "prescription_refill":
        return _api_error_response(
            400,
            "wrong_request_type",
            "Prescription eligibility requires intake.request.type to be refill.",
        )
    prescription_or_error = _prescription_from_intake(payload.intake)
    if isinstance(prescription_or_error, JSONResponse):
        return prescription_or_error
    patient_or_error = _resolve_patient_from_intake(payload.intake)
    if isinstance(patient_or_error, JSONResponse):
        return patient_or_error

    try:
        repo = SupabasePrescriptionEligibilityRepo()
        result = run_prescription_eligibility_check(
            patient_id=patient_or_error["id"],
            medication_name=prescription_or_error["medication_name"],
            dosage=prescription_or_error["dosage"],
            instructions=prescription_or_error["instructions"],
            task_id=payload.task_id,
            repo=repo,
        )
    except PrescriptionEligibilityError as exc:
        return _prescription_eligibility_error_response(exc)

    return result


def _prescription_eligibility_error_response(exc: PrescriptionEligibilityError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=prescription_error_payload(exc))


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
    if _normalize_intake_request_type(payload.intake.request.type) != "message_relay":
        return _api_error_response(
            400,
            "wrong_request_type",
            "Message relay requires intake.request.type to be message_relay.",
        )
    message = _compact_transcript(payload.intake.request.details or payload.intake.transcript)
    if not message:
        return _api_error_response(400, "missing_message", "Intake request details or transcript are required.")
    patient_or_error = _resolve_patient_from_intake(payload.intake)
    if isinstance(patient_or_error, JSONResponse):
        return patient_or_error

    try:
        repo = SupabaseMessageRelayRepo()
        result = run_message_relay_check(
            patient_id=patient_or_error["id"],
            first_name=payload.intake.first_name,
            last_name=payload.intake.last_name,
            dob=payload.intake.date_of_birth,
            message=message,
            task_id=payload.task_id,
            repo=repo,
        )
    except MessageRelayError as exc:
        return JSONResponse(status_code=exc.status_code, content=message_relay_error_payload(exc))

    return result


def _resolve_patient_from_intake(intake: IntakeExtraction) -> dict[str, Any] | JSONResponse:
    missing = [
        field
        for field, value in {
            "first_name": intake.first_name,
            "last_name": intake.last_name,
            "date_of_birth": intake.date_of_birth,
        }.items()
        if not value
    ]
    if missing:
        return _api_error_response(
            400,
            "missing_patient_identity",
            f"Intake is missing required patient identity fields: {', '.join(missing)}.",
        )

    try:
        repo = SupabaseSchedulerRepo()
        patient = repo.find_patient(intake.first_name or "", intake.last_name or "", intake.date_of_birth or "")
    except SchedulerError as exc:
        return JSONResponse(status_code=exc.status_code, content=scheduler_error_payload(exc))

    if not patient:
        return _api_error_response(
            404,
            "patient_not_found",
            "No patient matched intake first_name, last_name, and date_of_birth.",
        )
    return patient


def _normalize_intake_request_type(value: str | None) -> str:
    aliases = {
        "refill": "prescription_refill",
        "prescription_refill": "prescription_refill",
        "reschedule": "reschedule",
        "message_relay": "message_relay",
    }
    return aliases.get((value or "").strip().lower(), "unknown")


def _prescription_from_intake(intake: IntakeExtraction) -> dict[str, str] | JSONResponse:
    details = _compact_transcript(intake.request.details)
    order = next((item.strip() for item in intake.request.orders if item.strip()), "")
    if not order:
        return _api_error_response(
            400,
            "missing_prescription_order",
            "Intake request.orders must include the requested medication.",
        )

    dosage = _extract_dosage(f"{order} {details}")
    if not dosage:
        return _api_error_response(
            400,
            "missing_prescription_dosage",
            "Intake request details must include the requested prescription dosage.",
        )

    return {
        "medication_name": _strip_dosage(order),
        "dosage": dosage,
        "instructions": _extract_instructions(details, dosage),
    }


def _extract_dosage(text: str) -> str | None:
    match = re.search(r"\b(\d+(?:\.\d+)?)\s*(mg|milligrams?|g|grams?)\b", text, re.IGNORECASE)
    if not match:
        return None
    amount = match.group(1)
    unit = match.group(2).lower()
    normalized_unit = "mg" if unit.startswith("milligram") else "g" if unit.startswith("gram") else unit
    return f"{amount}{normalized_unit}"


def _strip_dosage(text: str) -> str:
    return re.sub(r"\b\d+(?:\.\d+)?\s*(?:mg|milligrams?|g|grams?)\b", "", text, flags=re.IGNORECASE).strip(" ,-")


def _extract_instructions(details: str, dosage: str) -> str:
    if not details:
        return ""
    dosage_match = re.fullmatch(r"(\d+(?:\.\d+)?)(mg|g)", dosage, re.IGNORECASE)
    if not dosage_match:
        return details
    amount, unit = dosage_match.groups()
    unit_pattern = r"(?:mg|milligrams?)" if unit.lower() == "mg" else r"(?:g|grams?)"
    dosage_pattern = rf"\b{re.escape(amount)}\s*{unit_pattern}\b"
    match = re.search(dosage_pattern, details, re.IGNORECASE)
    if match:
        after_dosage = details[match.end() :].strip(" ,.-")
        if after_dosage:
            return after_dosage
    return details
