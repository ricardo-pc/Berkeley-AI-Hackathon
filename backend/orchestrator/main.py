from __future__ import annotations

import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

import httpx
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from message_relay.errors import MessageRelayError
from message_relay.errors import error_payload as message_relay_error_payload
from message_relay.repo import SupabaseMessageRelayRepo
from message_relay.service import run_message_relay_check
from prescription_eligibility.errors import PrescriptionEligibilityError
from prescription_eligibility.errors import error_payload as prescription_error_payload
from prescription_eligibility.repo import SupabasePrescriptionEligibilityRepo
from prescription_eligibility.service import run_prescription_eligibility_check
from scheduling_eligibility.errors import ScheduleEligibilityError
from scheduling_eligibility.errors import error_payload as schedule_error_payload
from scheduling_eligibility.repo import SupabaseScheduleEligibilityRepo
from scheduling_eligibility.service import run_schedule_eligibility_check

try:
    from dotenv import find_dotenv, load_dotenv
except ImportError:  # pragma: no cover - python-dotenv is listed in requirements.
    find_dotenv = None
    load_dotenv = None


RequestType = Literal["refill", "reschedule", "message_relay", "unknown"]
UrgencySignal = Literal["routine", "urgent", "emergency", "unknown"]
APPOINTMENT_LENGTH_MINUTES = 30

TEXTBELT_URL = "https://textbelt.com/text"
# Symmetric to the success-path confirmation texts sent by backend/api's
# confirmation package once an action agent executes -- this is the
# escalated-instead-of-approved counterpart, sent right from this service
# since it owns the eligibility decision. Deliberately generic: never repeats
# the specific clinical/insurance reason over SMS, just asks the patient to
# call back.
DENIAL_NOUNS = {
    "prescription_refill": "prescription refill request",
    "reschedule": "appointment request",
}


class IntakeRequestDetails(BaseModel):
    type: RequestType = "unknown"
    details: str = ""
    orders: list[str] = Field(default_factory=list)
    preferred_times: list[dict[str, Any]] = Field(default_factory=list)
    urgency_signal: UrgencySignal = "unknown"


class IntakeExtraction(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: str | None = None
    phone_number: str | None = None
    insurance_plan: str | None = None
    request: IntakeRequestDetails = Field(default_factory=IntakeRequestDetails)
    requests: list[IntakeRequestDetails] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    transcript: str = ""

    def model_post_init(self, __context: Any) -> None:
        if not self.requests:
            self.requests = [self.request]
        elif _is_default_request(self.request):
            self.request = self.requests[0]


class OrchestratorRequest(BaseModel):
    intake: IntakeExtraction
    task_id: str | None = None


class OrchestratorRepo:
    def __init__(self, client: Any | None = None):
        self._client = client or _build_supabase_client()

    def find_patient(self, first_name: str, last_name: str, dob: str) -> dict[str, Any] | None:
        response = (
            self._client.table("patients")
            .select("*")
            .eq("first_name", first_name)
            .eq("last_name", last_name)
            .eq("date_of_birth", dob)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        return rows[0] if rows else None

    def get_next_scheduled_appointment(self, patient_id: str) -> dict[str, Any] | None:
        response = (
            self._client.table("appointments")
            .select("*")
            .eq("patient_id", patient_id)
            .eq("status", "scheduled")
            .gte("start_time", datetime.now(timezone.utc).isoformat())
            .order("start_time")
            .limit(1)
            .execute()
        )
        rows = response.data or []
        return rows[0] if rows else None


app = FastAPI(
    title="Clinic Orchestrator Service",
    version="0.1.0",
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/refill")
async def create_refill_check(payload: OrchestratorRequest):
    if _normalize_intake_request_type(payload.intake.request.type) != "prescription_refill":
        return _api_error_response(400, "wrong_request_type", "Refill requires intake.request.type to be refill.")

    patient_or_response = _resolve_patient_from_intake(payload.intake)
    if isinstance(patient_or_response, JSONResponse):
        return patient_or_response
    insurance_response = _insurance_escalation(patient_or_response, "prescription_refill")
    if insurance_response:
        return insurance_response

    prescription_or_response = _prescription_from_intake(payload.intake)
    if isinstance(prescription_or_response, JSONResponse):
        return prescription_or_response

    try:
        repo = SupabasePrescriptionEligibilityRepo()
        result = run_prescription_eligibility_check(
            patient_id=patient_or_response["id"],
            medication_name=prescription_or_response["medication_name"],
            dosage=prescription_or_response["dosage"],
            instructions=prescription_or_response["instructions"],
            task_id=payload.task_id,
            repo=repo,
        )
    except PrescriptionEligibilityError as exc:
        return JSONResponse(status_code=exc.status_code, content=prescription_error_payload(exc))

    result["denial_notice"] = _send_denial_notice("prescription_refill", result)
    return result


@app.post("/api/reschedule")
async def create_reschedule_check(payload: OrchestratorRequest):
    if _normalize_intake_request_type(payload.intake.request.type) != "reschedule":
        return _api_error_response(
            400,
            "wrong_request_type",
            "Reschedule requires intake.request.type to be reschedule.",
        )

    patient_or_response = _resolve_patient_from_intake(payload.intake)
    if isinstance(patient_or_response, JSONResponse):
        return patient_or_response
    insurance_response = _insurance_escalation(patient_or_response, "reschedule")
    if insurance_response:
        return insurance_response

    provider_id = patient_or_response.get("preferred_provider_id")
    if not provider_id:
        return _api_error_response(
            400,
            "missing_preferred_provider",
            "Patient does not have a preferred provider on file.",
        )

    start_or_response = _requested_start_from_intake(payload.intake)
    if isinstance(start_or_response, JSONResponse):
        return start_or_response
    requested_end = start_or_response + timedelta(minutes=APPOINTMENT_LENGTH_MINUTES)
    appointment_to_move = _next_scheduled_appointment(patient_or_response["id"])

    try:
        repo = SupabaseScheduleEligibilityRepo()
        result = run_schedule_eligibility_check(
            patient_id=patient_or_response["id"],
            provider_id=provider_id,
            requested_start=start_or_response,
            requested_end=requested_end,
            cancel_appointment_id=(appointment_to_move or {}).get("id"),
            task_id=payload.task_id,
            repo=repo,
        )
    except ScheduleEligibilityError as exc:
        return JSONResponse(status_code=exc.status_code, content=schedule_error_payload(exc))

    result["denial_notice"] = _send_denial_notice("reschedule", result)
    return result


@app.post("/api/message-relay")
async def create_message_relay_check(payload: OrchestratorRequest):
    if _normalize_intake_request_type(payload.intake.request.type) != "message_relay":
        return _api_error_response(
            400,
            "wrong_request_type",
            "Message relay requires intake.request.type to be message_relay.",
        )

    patient_or_response = _resolve_patient_from_intake(payload.intake)
    if isinstance(patient_or_response, JSONResponse):
        return patient_or_response
    insurance_response = _insurance_escalation(patient_or_response, "message_relay")
    if insurance_response:
        return insurance_response

    message = _compact_text(payload.intake.request.details or payload.intake.transcript)
    if not message:
        return _api_error_response(400, "missing_message", "Intake request details or transcript are required.")

    try:
        repo = SupabaseMessageRelayRepo()
        return run_message_relay_check(
            patient_id=patient_or_response["id"],
            first_name=payload.intake.first_name,
            last_name=payload.intake.last_name,
            dob=payload.intake.date_of_birth,
            message=message,
            task_id=payload.task_id,
            repo=repo,
        )
    except MessageRelayError as exc:
        return JSONResponse(status_code=exc.status_code, content=message_relay_error_payload(exc))


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

    repo = OrchestratorRepo()
    patient = repo.find_patient(intake.first_name or "", intake.last_name or "", intake.date_of_birth or "")
    if not patient:
        return _api_error_response(
            404,
            "patient_not_found",
            "No patient matched intake first_name, last_name, and date_of_birth.",
        )
    return patient


def _insurance_escalation(patient: dict[str, Any], task_type: str) -> dict[str, Any] | None:
    if patient.get("insurance_valid"):
        return None
    plan = patient.get("insurance_plan") or "unknown"
    return {
        "eligible": False,
        "status": "escalated",
        "flagged_reason": f"Insurance plan not accepted: {plan}.",
        "checks": {"insurance": {"valid": False, "plan": plan, "reason": "plan not accepted"}},
        "proposed_action": {"type": "escalate", "reason": "insurance plan not accepted"},
        "task_type": task_type,
    }


def _next_scheduled_appointment(patient_id: str) -> dict[str, Any] | None:
    return OrchestratorRepo().get_next_scheduled_appointment(patient_id)


def _requested_start_from_intake(intake: IntakeExtraction) -> datetime | JSONResponse:
    first = next((item for item in intake.request.preferred_times if isinstance(item, dict)), None)
    if not first or not first.get("date"):
        return _api_error_response(
            400,
            "missing_preferred_time",
            "Reschedule intake must include request.preferred_times[0].date.",
        )
    try:
        hour, minute = _time_from_preferred_time(first)
        year, month, day = (int(part) for part in first["date"].split("-"))
        return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return _api_error_response(
            400,
            "invalid_preferred_time",
            "Preferred time must include date YYYY-MM-DD and optional start_time HH:MM.",
        )


def _time_from_preferred_time(preferred_time: dict[str, Any]) -> tuple[int, int]:
    if preferred_time.get("start_time"):
        return tuple(int(part) for part in str(preferred_time["start_time"]).split(":", maxsplit=1))
    if preferred_time.get("time_of_day") == "afternoon":
        return 13, 0
    return 9, 0


def _prescription_from_intake(intake: IntakeExtraction) -> dict[str, str] | JSONResponse:
    details = _compact_text(intake.request.details)
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


def _normalize_intake_request_type(value: str | None) -> str:
    aliases = {
        "refill": "prescription_refill",
        "prescription_refill": "prescription_refill",
        "reschedule": "reschedule",
        "message_relay": "message_relay",
    }
    return aliases.get((value or "").strip().lower(), "unknown")


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


def _compact_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _api_error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": {"code": code, "message": message}})


def _is_default_request(request: IntakeRequestDetails) -> bool:
    return (
        request.type == "unknown"
        and request.details == ""
        and request.orders == []
        and request.preferred_times == []
        and request.urgency_signal == "unknown"
    )


def load_environment() -> None:
    if not find_dotenv or not load_dotenv:
        return
    env_path = find_dotenv(usecwd=True)
    if env_path:
        load_dotenv(env_path)


def _build_denial_message(task_type: str, first_name: str | None) -> str | None:
    noun = DENIAL_NOUNS.get(task_type)
    if noun is None:
        return None
    name = first_name or "there"
    return (
        f"Hi {name}, we're unable to process your {noun} automatically. "
        "Please call our office back so we can assist you."
    )


def _send_denial_notice(task_type: str, result: dict[str, Any]) -> dict[str, Any] | None:
    """Best-effort: texts the patient to call back when this check escalates instead of approving."""
    if result.get("status") != "escalated":
        return None

    patient = result.get("patient") or {}
    phone_number = patient.get("phone")
    message = _build_denial_message(task_type, patient.get("first_name"))
    if message is None:
        return None
    if not phone_number:
        return {"sent": False, "reason": "no phone number on file"}

    load_environment()
    api_key = os.getenv("TEXTBELT_API_KEY")
    if not api_key:
        return {"sent": False, "reason": "TEXTBELT_API_KEY not configured"}

    try:
        response = httpx.post(
            TEXTBELT_URL,
            data={"phone": phone_number, "message": message, "key": api_key},
            timeout=15.0,
        )
        data = response.json()
    except httpx.HTTPError as exc:
        return {"sent": False, "reason": str(exc)}

    if not data.get("success"):
        return {"sent": False, "reason": data.get("error") or "unknown error"}

    return {"sent": True, "sid": data.get("textId"), "to": phone_number, "body": message}


def _build_supabase_client() -> Any:
    load_environment()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        return _raise_config_error()

    from supabase import create_client

    return create_client(url, key)


def _raise_config_error() -> None:
    raise RuntimeError("Supabase URL/service role key not configured.")
