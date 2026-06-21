from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

from .repo import SummaryRepo


def build_daily_digest(
    *,
    since: datetime | None,
    repo: SummaryRepo,
    summarize: Callable[[dict[str, Any]], str] | None = None,
) -> dict[str, Any]:
    """Read-only digest over the tasks table -- no LLM required for the structured part.

    Buckets by status: completed (any task_type -- covers "who was scheduled" plus
    refills and relayed messages), flagged (escalated, with the reason a CHW needs
    to act on), pending (still awaiting one-click approval). Missing-insurance comes
    from patients.insurance_valid directly rather than agent_checks, since not every
    agent path writes an "insurance" key into agent_checks.
    """
    tasks = repo.get_tasks(since)
    patient_ids = [task.get("patient_id") for task in tasks if task.get("patient_id")]
    patients = repo.get_patients(patient_ids)

    completed = []
    flagged = []
    pending = []

    for task in tasks:
        entry = {
            "patient_name": _patient_name(patients.get(task.get("patient_id"))),
            "task_type": task.get("task_type"),
            "summary": task.get("agent_summary"),
        }
        status = task.get("status")
        if status == "complete":
            completed.append(entry)
        elif status == "escalated":
            flagged.append({**entry, "flagged_reason": task.get("flagged_reason")})
        elif status == "pending_approval":
            pending.append(entry)

    missing_insurance = [
        {"patient_name": _patient_name(patient), "insurance_plan": patient.get("insurance_plan")}
        for patient in repo.get_patients_with_invalid_insurance()
    ]

    digest = {
        "completed": completed,
        "flagged": flagged,
        "pending": pending,
        "missing_insurance": missing_insurance,
        "counts": {
            "completed": len(completed),
            "flagged": len(flagged),
            "pending": len(pending),
            "missing_insurance": len(missing_insurance),
            "total_tasks": len(tasks),
        },
    }

    if summarize:
        digest["narrative"] = summarize(digest)

    return digest


def _patient_name(patient: dict[str, Any] | None) -> str:
    if not patient:
        return "Unknown patient"
    return f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip() or "Unknown patient"
