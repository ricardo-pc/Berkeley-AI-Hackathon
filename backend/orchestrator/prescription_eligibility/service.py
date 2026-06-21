from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .checks import (
    check_conflicting_medication,
    check_dosage_match,
    check_recent_visit,
    check_upcoming_visit,
    determine_visit_window_months,
    find_identical_prior_prescription,
)
from .errors import PatientNotFoundError
from .repo import PrescriptionEligibilityRepo


def run_prescription_eligibility_check(
    *,
    patient_id: str,
    medication_name: str,
    dosage: str,
    instructions: str,
    repo: PrescriptionEligibilityRepo,
    task_id: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)

    patient = repo.get_patient(patient_id)
    if not patient:
        raise PatientNotFoundError(patient_id)

    appointments = repo.get_appointments(patient_id)
    window_months = determine_visit_window_months(
        datetime.fromisoformat(str(patient["date_of_birth"])), now=now
    )
    has_recent_visit, last_visit = check_recent_visit(
        appointments=appointments, window_months=window_months, now=now
    )
    has_upcoming_visit = check_upcoming_visit(appointments=appointments, now=now)

    prescriptions = repo.get_prescriptions(patient_id)
    ever_prescribed, dosage_match = check_dosage_match(
        medication_name=medication_name,
        dosage=dosage,
        instructions=instructions,
        prior_prescriptions=prescriptions,
    )
    active_prescriptions = [p for p in prescriptions if p.get("active")]
    conflict, conflict_medication = check_conflicting_medication(
        medication_name=medication_name,
        active_prescriptions=active_prescriptions,
    )

    eligible = has_recent_visit and has_upcoming_visit and ever_prescribed and dosage_match
    matching_prescription = find_identical_prior_prescription(
        medication_name=medication_name,
        dosage=dosage,
        instructions=instructions,
        prior_prescriptions=prescriptions,
    )

    prescription_checks = {
        "eligible": eligible,
        "medication": medication_name,
        "requested_dosage": dosage,
        "requested_instructions": instructions,
        "visit_window_months": window_months,
        "has_recent_visit": has_recent_visit,
        "last_visit": last_visit,
        "has_upcoming_visit": has_upcoming_visit,
        "ever_prescribed": ever_prescribed,
        "dosage_match": dosage_match,
        "identical_prior_prescription_id": (matching_prescription or {}).get("id"),
        "conflict": conflict,
        "conflict_medication": conflict_medication,
    }
    checks = {
        "prescription": prescription_checks,
    }

    status = "pending_approval" if eligible else "escalated"
    flagged_reason = None if eligible else _ineligibility_reason(
        has_recent_visit=has_recent_visit,
        has_upcoming_visit=has_upcoming_visit,
        ever_prescribed=ever_prescribed,
        dosage_match=dosage_match,
    )

    proposed_action = None
    if eligible:
        proposed_action = {
            "type": "prescription_refill",
            "medication_name": medication_name,
            "dosage": dosage,
            "instructions": instructions,
            "provider_id": (
                matching_prescription.get("provider_id") if matching_prescription else None
            ),
            "patient_id": patient_id,
        }

    result = {
        "eligible": eligible,
        "status": status,
        "flagged_reason": flagged_reason,
        "checks": checks,
        "proposed_action": proposed_action,
    }

    if task_id:
        existing_task = repo.get_task(task_id)
        merged_checks = {**(existing_task.get("agent_checks") or {}), **checks}
        repo.update_task(
            task_id,
            {
                "status": status,
                "agent_summary": None,
                "agent_checks": merged_checks,
                "proposed_action": proposed_action,
                "flagged_reason": flagged_reason,
            },
        )

    return result


def _ineligibility_reason(
    *,
    has_recent_visit: bool,
    has_upcoming_visit: bool,
    ever_prescribed: bool,
    dosage_match: bool,
) -> str:
    reasons = []
    if not ever_prescribed:
        reasons.append("patient has not been prescribed this medication before")
    elif not dosage_match:
        reasons.append("requested dosage/instructions do not match the prior prescription")
    if not has_recent_visit:
        reasons.append("no visit within the required recent-visit window")
    if not has_upcoming_visit:
        reasons.append("no upcoming visit scheduled within the next year")
    return "; ".join(reasons)
