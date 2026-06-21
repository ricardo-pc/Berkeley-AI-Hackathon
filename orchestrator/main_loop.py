from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
API_ROOT = REPO_ROOT / "backend" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from backend.eligibility_service.scheduling_eligibility.checks import check_calendar_conflict
from backend.eligibility_service.scheduling_eligibility.service import run_schedule_eligibility_check

from .demo_fixtures import APPOINTMENTS, PATIENTS, PRESCRIPTIONS, PROVIDERS, REFERENCE_NOW


REQUIRED_INTAKE_FIELDS = ["first_name", "last_name", "date_of_birth", "phone_number", "insurance_plan"]
DEFAULT_PROVIDER_ID = "b1b2c3d4-0001-0001-0001-000000000001"

# Checked against every voicemail's transcript, regardless of request type --
# a refill or reschedule call can mention these just as easily as a message
# relay, and an emergency must bypass automation no matter how the caller
# framed their request.
EMERGENCY_PHRASES = ["chest pain", "cannot breathe", "stroke", "unconscious", "emergency"]


class DemoScheduleRepo:
    def get_provider(self, provider_id: str) -> dict[str, Any]:
        return next((provider for provider in PROVIDERS if provider["id"] == provider_id), {})

    def get_scheduled_appointments(self, provider_id: str) -> list[dict[str, Any]]:
        return [
            appointment
            for appointment in APPOINTMENTS
            if appointment["provider_id"] == provider_id and appointment["status"] == "scheduled"
        ]

    def get_reschedule_tasks_since_last_visit(self, patient_id: str) -> list[dict[str, Any]]:
        return []

    def update_task(self, task_id: str, fields: dict[str, Any]) -> None:
        return None


def run_directory(input_dir: Path) -> list[dict[str, Any]]:
    return [run_intake_file(path) for path in sorted(input_dir.glob("*.json"))]


def run_intake_file(path: Path) -> dict[str, Any]:
    intake = json.loads(path.read_text(encoding="utf-8"))
    result = run_intake(intake)
    result["source_file"] = str(path)
    return result


def run_intake(intake: dict[str, Any]) -> dict[str, Any]:
    request = intake.get("request") or {}
    task_type = _normalize_task_type(request.get("type"))
    patient = _resolve_patient(intake)

    if _has_any(intake.get("transcript") or "", EMERGENCY_PHRASES):
        return _task(
            intake=intake,
            patient=patient,
            task_type="escalate",
            status="escalated",
            agent_checks={"triage": {"emergency_signal": True}},
            flagged_reason="Emergency symptoms mentioned in voicemail — bypasses automation, call immediately.",
            proposed_action={"type": "escalate", "reason": "emergency symptoms mentioned"},
        )

    missing_fields = _missing_fields(intake)

    agent_checks: dict[str, Any] = {
        "intake_eval": {
            "valid_json": True,
            "missing_fields": missing_fields,
            "request_type": task_type,
            "patient_resolved": bool(patient),
        }
    }

    if missing_fields:
        return _task(
            intake=intake,
            patient=patient,
            task_type=task_type,
            status="escalated",
            agent_checks=agent_checks,
            flagged_reason=f"Missing required intake fields: {', '.join(missing_fields)}.",
        )

    if not patient:
        return _task(
            intake=intake,
            patient=None,
            task_type=task_type,
            status="escalated",
            agent_checks=agent_checks,
            flagged_reason="Patient could not be matched to the demo database.",
        )

    insurance_check = {
        "valid": bool(patient["insurance_valid"]),
        "plan": patient["insurance_plan"],
    }
    if not patient["insurance_valid"]:
        insurance_check["reason"] = "plan not accepted"
    agent_checks["insurance"] = insurance_check

    if not patient["insurance_valid"]:
        return _task(
            intake=intake,
            patient=patient,
            task_type=task_type,
            status="escalated",
            agent_checks=agent_checks,
            flagged_reason=f"Insurance plan not accepted: {patient['insurance_plan']}.",
            proposed_action={"type": "escalate", "reason": "insurance plan not accepted"},
        )

    if task_type == "prescription_refill":
        return _run_prescription(intake, patient, agent_checks)
    if task_type == "reschedule":
        return _run_reschedule(intake, patient, agent_checks)
    if task_type == "message_relay":
        return _run_message_relay(intake, patient, agent_checks)

    return _task(
        intake=intake,
        patient=patient,
        task_type=task_type,
        status="escalated",
        agent_checks=agent_checks,
        flagged_reason="Request type is unknown.",
    )


def _run_prescription(intake: dict[str, Any], patient: dict[str, Any], agent_checks: dict[str, Any]) -> dict[str, Any]:
    request = intake.get("request") or {}
    order = (request.get("orders") or [""])[0]
    order_context = f"{order} {request.get('details') or ''}".strip()
    prescription = _match_prescription(patient["id"], order)
    last_visit = _last_visit(patient["id"])
    active_meds = [p["medication_name"] for p in PRESCRIPTIONS if p["patient_id"] == patient["id"] and p["active"]]

    if not prescription:
        agent_checks["prescription"] = {"eligible": False, "order": order, "reason": "medication not active"}
        return _task(
            intake=intake,
            patient=patient,
            task_type="prescription_refill",
            status="escalated",
            agent_checks=agent_checks,
            flagged_reason="Requested medication was not found as an active prescription.",
            proposed_action={"type": "escalate", "reason": "medication not active"},
        )

    dosage_match = _normalize_dosage(prescription["dosage"]) in _normalize_dosage(order_context)
    visit_recent = bool(last_visit and REFERENCE_NOW - last_visit <= timedelta(days=183))
    conflict_medication = "Amlodipine" if prescription["medication_name"] == "Lisinopril" and "Amlodipine" in active_meds else None
    eligible = dosage_match and visit_recent

    agent_checks["prescription"] = {
        "eligible": eligible,
        "medication": prescription["medication_name"],
        "dosage_match": dosage_match,
        "requested_order": order,
        "active_dosage": prescription["dosage"],
        "last_visit": last_visit.date().isoformat() if last_visit else None,
        "recent_visit": visit_recent,
        "conflict": bool(conflict_medication),
        "conflict_medication": conflict_medication,
    }

    if not dosage_match:
        reason = "requested dosage does not match active prescription"
    elif not visit_recent:
        reason = "last visit exceeds 6 month eligibility window"
    else:
        reason = None

    return _task(
        intake=intake,
        patient=patient,
        task_type="prescription_refill",
        status="pending_approval" if eligible else "escalated",
        agent_checks=agent_checks,
        flagged_reason=reason,
        proposed_action=(
            {
                "type": "prescription_refill",
                "medication_name": prescription["medication_name"],
                "dosage": prescription["dosage"],
                "instructions": prescription["instructions"],
                "provider_id": prescription["provider_id"],
                "patient_id": patient["id"],
            }
            if eligible
            else {"type": "escalate", "reason": reason}
        ),
    )


def _run_reschedule(intake: dict[str, Any], patient: dict[str, Any], agent_checks: dict[str, Any]) -> dict[str, Any]:
    requested_start = _parse_requested_start(intake)
    requested_end = requested_start + timedelta(minutes=30)
    repo = DemoScheduleRepo()

    scheduling = run_schedule_eligibility_check(
        patient_id=patient["id"],
        provider_id=DEFAULT_PROVIDER_ID,
        requested_start=requested_start,
        requested_end=requested_end,
        repo=repo,
    )
    agent_checks.update(scheduling["checks"])

    if scheduling["eligible"]:
        return _task(
            intake=intake,
            patient=patient,
            task_type="reschedule",
            status=scheduling["status"],
            agent_checks=agent_checks,
            proposed_action={
                **scheduling["proposed_action"],
                "cancel_appointment_id": _appointment_to_move(patient["id"]),
            },
        )

    alternative = _find_next_slot(DEFAULT_PROVIDER_ID, requested_start + timedelta(days=1))
    proposed_action = None
    if alternative:
        start, end = alternative
        proposed_action = {
            "type": "reschedule",
            "cancel_appointment_id": _appointment_to_move(patient["id"]),
            "new_start": start.isoformat(),
            "new_end": end.isoformat(),
            "provider_id": DEFAULT_PROVIDER_ID,
        }
        agent_checks["scheduling_eligibility"]["proposed_alternative_slot"] = {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "provider_id": DEFAULT_PROVIDER_ID,
        }

    return _task(
        intake=intake,
        patient=patient,
        task_type="reschedule",
        status="pending_approval" if proposed_action else scheduling["status"],
        agent_checks=agent_checks,
        flagged_reason=scheduling["flagged_reason"],
        proposed_action=proposed_action,
    )


def _run_message_relay(intake: dict[str, Any], patient: dict[str, Any], agent_checks: dict[str, Any]) -> dict[str, Any]:
    # Emergency phrases are already caught upstream in run_intake(), before
    # task_type dispatch even happens -- nothing left to check for here.
    transcript = intake.get("transcript") or ""
    adverse_reaction = _has_any(transcript, ["dizzy", "dizziness", "nauseous", "nausea", "reaction"])
    agent_checks["message"] = {"adverse_reaction_reported": adverse_reaction}

    return _task(
        intake=intake,
        patient=patient,
        task_type="message_relay",
        status="pending_approval",
        agent_checks=agent_checks,
        proposed_action={
            "type": "message_relay",
            "provider_id": DEFAULT_PROVIDER_ID,
            "patient_id": patient["id"],
            "message": _message_body(intake),
        },
    )


def _task(
    *,
    intake: dict[str, Any],
    patient: dict[str, Any] | None,
    task_type: str,
    status: str,
    agent_checks: dict[str, Any],
    flagged_reason: str | None = None,
    proposed_action: dict[str, Any] | None = None,
) -> dict[str, Any]:
    summary = _summary(intake, patient, task_type, status, flagged_reason, proposed_action)
    return {
        "patient_id": patient["id"] if patient else None,
        "patient_name": _patient_name(intake),
        "task_type": task_type,
        "status": status,
        "agent_summary": summary,
        "agent_checks": agent_checks,
        "proposed_action": proposed_action,
        "flagged_reason": flagged_reason,
    }


def _summary(
    intake: dict[str, Any],
    patient: dict[str, Any] | None,
    task_type: str,
    status: str,
    flagged_reason: str | None,
    proposed_action: dict[str, Any] | None,
) -> str:
    name = _patient_name(intake)
    if status == "escalated":
        return f"{name} needs manual review: {flagged_reason}"
    if task_type == "reschedule" and proposed_action:
        return f"{name} can be rescheduled to {proposed_action['new_start']}."
    if task_type == "prescription_refill" and proposed_action:
        return f"{name} is eligible for a {proposed_action['medication_name']} refill."
    if task_type == "message_relay":
        return f"{name}'s message is ready to relay to the provider."
    return f"{name}'s request is ready for review."


def _missing_fields(intake: dict[str, Any]) -> list[str]:
    fields = set(intake.get("missing_fields") or [])
    fields.update(field for field in REQUIRED_INTAKE_FIELDS if not intake.get(field))
    return sorted(fields)


def _resolve_patient(intake: dict[str, Any]) -> dict[str, Any] | None:
    first = (intake.get("first_name") or "").lower()
    last = (intake.get("last_name") or "").lower()
    dob = intake.get("date_of_birth")
    return next(
        (
            patient
            for patient in PATIENTS
            if patient["first_name"].lower() == first
            and patient["last_name"].lower() == last
            and patient["date_of_birth"] == dob
        ),
        None,
    )


def _normalize_task_type(value: str | None) -> str:
    if value == "refill":
        return "prescription_refill"
    if value in {"reschedule", "message_relay"}:
        return value
    return "unknown"


def _match_prescription(patient_id: str, order: str) -> dict[str, Any] | None:
    normalized = order.lower()
    return next(
        (
            prescription
            for prescription in PRESCRIPTIONS
            if prescription["patient_id"] == patient_id
            and prescription["active"]
            and prescription["medication_name"].lower() in normalized
        ),
        None,
    )


def _last_visit(patient_id: str) -> datetime | None:
    visits = [
        datetime.fromisoformat(appointment["start_time"])
        for appointment in APPOINTMENTS
        if appointment["patient_id"] == patient_id and datetime.fromisoformat(appointment["start_time"]) <= REFERENCE_NOW
    ]
    return max(visits) if visits else None


def _appointment_to_move(patient_id: str) -> str | None:
    future = [
        appointment
        for appointment in APPOINTMENTS
        if appointment["patient_id"] == patient_id and datetime.fromisoformat(appointment["start_time"]) >= REFERENCE_NOW
    ]
    if not future:
        return None
    return min(future, key=lambda appointment: appointment["start_time"])["id"]


def _parse_requested_start(intake: dict[str, Any]) -> datetime:
    preferred_times = (intake.get("request") or {}).get("preferred_times") or []
    first = preferred_times[0] if preferred_times else None

    # Current intake agent output: structured {raw_text, date, start_time, time_of_day}
    # with relative dates already resolved. Prefer this over text parsing.
    if isinstance(first, dict) and first.get("date"):
        year, month, day = (int(part) for part in first["date"].split("-"))
        if first.get("start_time"):
            hour, minute = (int(part) for part in first["start_time"].split(":"))
        elif first.get("time_of_day") == "afternoon":
            hour, minute = 13, 0
        else:
            hour, minute = 9, 0
        return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)

    # Fallback: older plain-text preferred_times, or no structured field at all.
    text = " ".join(t for t in preferred_times if isinstance(t, str))
    if not text:
        text = (intake.get("request") or {}).get("details") or ""

    month = 6 if re.search(r"\bjune\b", text, re.IGNORECASE) else REFERENCE_NOW.month
    day_match = re.search(r"\b(\d{1,2})(?:st|nd|rd|th)?\b", text)
    day = int(day_match.group(1)) if day_match else REFERENCE_NOW.day
    hour = 9
    hour_match = re.search(r"\b(\d{1,2})(?::\d{2})?\s*(?:am|pm|a\.m\.|p\.m\.)?\b", text, re.IGNORECASE)
    if hour_match:
        hour = int(hour_match.group(1))
    if re.search(r"\b(pm|p\.m\.|afternoon)\b", text, re.IGNORECASE) and hour < 12:
        hour += 12
    if re.search(r"\bmorning\b", text, re.IGNORECASE):
        hour = 9
    return datetime(REFERENCE_NOW.year, month, day, hour, 0, tzinfo=timezone.utc)


def _find_next_slot(provider_id: str, start_after: datetime) -> tuple[datetime, datetime] | None:
    repo = DemoScheduleRepo()
    provider = repo.get_provider(provider_id)
    cursor = start_after.replace(hour=9, minute=0, second=0, microsecond=0)
    for day_offset in range(14):
        day = cursor + timedelta(days=day_offset)
        for hour in range(9, 17):
            start = day.replace(hour=hour)
            end = start + timedelta(minutes=30)
            conflict, _reason = check_calendar_conflict(
                requested_start=start,
                requested_end=end,
                provider_availability=provider["availability"],
                existing_appointments=repo.get_scheduled_appointments(provider_id),
            )
            if not conflict:
                return start, end
    return None


def _normalize_dosage(value: str) -> str:
    normalized = value.lower()
    normalized = re.sub(r"\bmilligrams?\b", "mg", normalized)
    normalized = re.sub(r"\s+", "", normalized)
    return normalized


def _has_any(text: str, phrases: list[str]) -> bool:
    normalized = text.lower()
    return any(phrase in normalized for phrase in phrases)


def _message_body(intake: dict[str, Any]) -> str:
    details = (intake.get("request") or {}).get("details")
    return details or intake.get("transcript") or ""


def _patient_name(intake: dict[str, Any]) -> str:
    return " ".join(part for part in [intake.get("first_name"), intake.get("last_name")] if part) or "Unknown patient"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run demo intake evals and eligibility checks.")
    parser.add_argument(
        "--input-dir",
        default=str(REPO_ROOT / "demo" / "intake_output"),
        help="Directory of *.intake.json files.",
    )
    parser.add_argument("--output", help="Optional path to write orchestrator results JSON.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    results = run_directory(Path(args.input_dir))
    output = json.dumps(results, indent=2 if args.pretty else None)
    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
