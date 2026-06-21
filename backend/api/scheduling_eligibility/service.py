from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

from .checks import check_calendar_conflict, check_consecutive_reschedules
from .claude_summary import generate_agent_summary
from .errors import ProviderNotFoundError
from .repo import ScheduleEligibilityRepo

MANUAL_CALL_REASON = (
    "Patient has made more than 2 consecutive reschedule requests without completing a visit — "
    "call to confirm the reason before adjusting the schedule again."
)


def run_schedule_eligibility_check(
    *,
    patient_id: str,
    provider_id: str,
    requested_start: datetime,
    requested_end: datetime,
    repo: ScheduleEligibilityRepo,
    cancel_appointment_id: str | None = None,
    task_id: str | None = None,
    summarize: Callable[[dict[str, Any]], str] = generate_agent_summary,
) -> dict[str, Any]:
    provider = repo.get_provider(provider_id)
    if not provider:
        raise ProviderNotFoundError(provider_id)

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
        }
    }

    eligible = not conflict and not requires_manual_call
    status = "escalated" if requires_manual_call else "pending_approval"
    flagged_reason = MANUAL_CALL_REASON if requires_manual_call else None

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

    agent_summary = summarize(checks)

    result = {
        "eligible": eligible,
        "status": status,
        "flagged_reason": flagged_reason,
        "agent_checks": checks,
        "agent_summary": agent_summary,
        "suggested_timeslot": suggested_timeslot,
        "proposed_action": proposed_action,
    }

    if task_id:
        repo.update_task(
            task_id,
            {
                "status": status,
                "agent_summary": agent_summary,
                "agent_checks": checks,
                "proposed_action": proposed_action,
                "flagged_reason": flagged_reason,
            },
        )

    return result
