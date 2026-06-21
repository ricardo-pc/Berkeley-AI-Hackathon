from __future__ import annotations

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse

from prescription_eligibility.errors import PrescriptionEligibilityError
from prescription_eligibility.errors import error_payload as prescription_error_payload
from prescription_eligibility.repo import SupabasePrescriptionEligibilityRepo
from prescription_eligibility.schemas import PrescriptionEligibilityRequest
from prescription_eligibility.service import run_prescription_eligibility_check
from scheduling_eligibility.errors import ScheduleEligibilityError
from scheduling_eligibility.errors import error_payload as schedule_error_payload
from scheduling_eligibility.repo import SupabaseScheduleEligibilityRepo
from scheduling_eligibility.schemas import ScheduleEligibilityRequest
from scheduling_eligibility.service import run_schedule_eligibility_check
from transcription.errors import InvalidAudioError, TranscriptionError, error_payload
from transcription.schemas import TranscriptionResponse, to_plain_dict
from transcription.service import transcribe_audio


app = FastAPI(
    title="Clinic Voicemail Speech-to-Text API",
    version="0.1.0",
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


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


def _error_response(exc: TranscriptionError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=error_payload(exc))


@app.post("/api/schedule-eligibility")
async def create_schedule_eligibility_check(payload: ScheduleEligibilityRequest):
    try:
        repo = SupabaseScheduleEligibilityRepo()
        result = run_schedule_eligibility_check(
            patient_id=payload.patient_id,
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
async def create_prescription_eligibility_check(payload: PrescriptionEligibilityRequest):
    try:
        repo = SupabasePrescriptionEligibilityRepo()
        result = run_prescription_eligibility_check(
            patient_id=payload.patient_id,
            medication_name=payload.medication_name,
            dosage=payload.dosage,
            instructions=payload.instructions,
            task_id=payload.task_id,
            repo=repo,
        )
    except PrescriptionEligibilityError as exc:
        return _prescription_eligibility_error_response(exc)

    return result


def _prescription_eligibility_error_response(exc: PrescriptionEligibilityError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=prescription_error_payload(exc))

