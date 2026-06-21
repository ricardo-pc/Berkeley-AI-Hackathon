from __future__ import annotations

from fastapi import FastAPI
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


app = FastAPI(
    title="Clinic Eligibility Service",
    version="0.1.0",
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/prescription-eligibility")
async def create_prescription_eligibility_check(payload: PrescriptionEligibilityRequest):
    try:
        repo = SupabasePrescriptionEligibilityRepo()
        return run_prescription_eligibility_check(
            patient_id=payload.patient_id,
            medication_name=payload.medication_name,
            dosage=payload.dosage,
            instructions=payload.instructions,
            task_id=payload.task_id,
            repo=repo,
        )
    except PrescriptionEligibilityError as exc:
        return JSONResponse(status_code=exc.status_code, content=prescription_error_payload(exc))


@app.post("/api/schedule-eligibility")
async def create_schedule_eligibility_check(payload: ScheduleEligibilityRequest):
    try:
        repo = SupabaseScheduleEligibilityRepo()
        return run_schedule_eligibility_check(
            patient_id=payload.patient_id,
            provider_id=payload.provider_id,
            requested_start=payload.requested_start,
            requested_end=payload.requested_end,
            cancel_appointment_id=payload.cancel_appointment_id,
            task_id=payload.task_id,
            repo=repo,
        )
    except ScheduleEligibilityError as exc:
        return JSONResponse(status_code=exc.status_code, content=schedule_error_payload(exc))
