from __future__ import annotations

from datetime import datetime
from typing import Any

from .checks import check_calendar_conflict, check_consecutive_reschedules, find_next_available_slot
from .errors import PatientNotFoundError, ProviderNotFoundError
from .repo import ScheduleEligibilityRepo

MANUAL_CALL_REASON = (
    "Patient has made more than 2 consecutive reschedule requests without completing a visit — "
    "call to confirm the reason before adjusting the schedule again."
)
NO_ALTERNATIVE_SLOT_REASON = "No available slot found in the next two weeks — needs manual scheduling assistance."


def run_schedule_eligibility_check(
    *,
    patient_id: str,
    provider_id: str,
    requested_start: datetime,
    requested_end: datetime,
    repo: ScheduleEligibilityRepo,
    cancel_appointment_id: str | None = None,
    task_id: str | None = None,
) -> dict[str, Any]:
    provider = repo.get_provider(provider_id)
    if not provider:
        raise ProviderNotFoundError(provider_id)

    patient = repo.get_patient(patient_id)
    if not patient:
        raise PatientNotFoundError(patient_id)

    appointments = repo.get_scheduled_appointments(provider_id)
    conflict, conflict_reason = check_calendar_conflict(
        requested_start=requested_start,
        requested_end=requested_end,
        provider_availability=provider.get("availability") or {},
        existing_appointments=appointments,
        exclude_appointment_id=cancel_appointment_id,
    )

    reschedule_tasks = repo.get_reschedule_tasks_since_last_visit(patient_id)
    consecutive_count, requires_manual_call = check_consecutive_reschedules(
        reschedule_tasks_since_last_visit=reschedule_tasks,
    )

    searched_for_alternative = conflict and not requires_manual_call
    alternative_slot = None
    if searched_for_alternative:
        alternative_slot = find_next_available_slot(
            requested_start=requested_start,
            duration=requested_end - requested_start,
            provider_availability=provider.get("availability") or {},
            existing_appointments=appointments,
            exclude_appointment_id=cancel_appointment_id,
        )

    checks = {
        "scheduling_eligibility": {
            "requested_slot": {
                "start": requested_start.isoformat(),
                "end": requested_end.isoformat(),
            },
            "provider_id": provider_id,
            "conflict": conflict,
            "conflict_reason": conflict_reason,
            "consecutive_reschedule_count": consecutive_count,
            "requires_manual_call": requires_manual_call,
            "alternative_slot_found": (alternative_slot is not None) if searched_for_alternative else None,
        }
    }

    eligible = not conflict and not requires_manual_call

    if requires_manual_call:
        status = "escalated"
        flagged_reason = MANUAL_CALL_REASON
    elif conflict and alternative_slot is None:
        status = "escalated"
        flagged_reason = NO_ALTERNATIVE_SLOT_REASON
    else:
        status = "pending_approval"
        flagged_reason = None

    suggested_timeslot = None
    proposed_action = None
    if eligible:
        suggested_timeslot = {
            "start": requested_start.isoformat(),
            "end": requested_end.isoformat(),
            "provider_id": provider_id,
        }
        proposed_action = {
            "type": "reschedule",
            "cancel_appointment_id": cancel_appointment_id,
            "new_start": requested_start.isoformat(),
            "new_end": requested_end.isoformat(),
            "provider_id": provider_id,
        }
    elif alternative_slot is not None:
        alt_start, alt_end = alternative_slot
        suggested_timeslot = {
            "start": alt_start.isoformat(),
            "end": alt_end.isoformat(),
            "provider_id": provider_id,
        }
        proposed_action = {
            "type": "reschedule",
            "cancel_appointment_id": cancel_appointment_id,
            "new_start": alt_start.isoformat(),
            "new_end": alt_end.isoformat(),
            "provider_id": provider_id,
        }

    result = {
        "eligible": eligible,
        "status": status,
        "flagged_reason": flagged_reason,
        "checks": checks,
        "suggested_timeslot": suggested_timeslot,
        "proposed_action": proposed_action,
        "patient": {
            "id": patient.get("id", patient_id),
            "first_name": patient.get("first_name"),
            "phone": patient.get("phone"),
        },
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
