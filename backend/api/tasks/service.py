"""The single decision executor for the CHW dashboard.

`apply_decision` is the one entry point: it reads the task, then dispatches
approvals to the right action handler (refill / reschedule / relay) as plain
function calls — reusing the existing fulfillment/scheduler services rather
than separate HTTP endpoints. Reject/action_taken/mark_done/reopen are status
writes. Output `Task` dicts match the dashboard's lib/types.ts shape 1:1.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .repo import TasksRepo

CHW_DEFAULT = "Riya Shah"
ACTIONABLE = {"prescription_refill", "reschedule", "message_relay"}
ALLOWED_TYPES = ACTIONABLE | {"escalate"}
KNOWN_STATUS = {"pending_approval", "escalated", "rejected", "complete"}
REOPEN_STATUSES = {"pending_approval", "escalated"}
DECISIONS = {"approve", "reject", "action_taken", "mark_done", "reopen"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------- mapping ----
def map_task(
    row: dict[str, Any], patients: dict[str, dict], voicemails: dict[str, dict]
) -> dict[str, Any]:
    patient = patients.get(row.get("patient_id")) if row.get("patient_id") else None
    vm = voicemails.get(row.get("voicemail_id")) if row.get("voicemail_id") else None
    name = "Unknown patient"
    if patient:
        name = " ".join(x for x in [patient.get("first_name"), patient.get("last_name")] if x).strip() or name

    task_type = row.get("task_type") if row.get("task_type") in ALLOWED_TYPES else "escalate"
    status = row.get("status") if row.get("status") in KNOWN_STATUS else "escalated"

    return {
        "id": row["id"],
        "patient_id": row.get("patient_id"),
        "patient_name": name,
        "task_type": task_type,
        "status": status,
        "agent_summary": row.get("agent_summary") or "",
        "agent_checks": row.get("agent_checks") or {},
        "proposed_action": row.get("proposed_action"),
        "flagged_reason": row.get("flagged_reason"),
        "created_at": row.get("created_at"),
        "chw_note": row.get("chw_note"),
        "reviewed_at": row.get("reviewed_at"),
        "approved_at": row.get("approved_at"),
        "rejected_at": row.get("rejected_at"),
        "transcript": (vm or {}).get("transcript"),
        "patient_dob": (patient or {}).get("date_of_birth"),
        "patient_phone": (patient or {}).get("phone"),
    }


def list_tasks(repo: TasksRepo) -> list[dict[str, Any]]:
    rows = repo.list_tasks()
    pids = list({r.get("patient_id") for r in rows if r.get("patient_id")})
    vids = list({r.get("voicemail_id") for r in rows if r.get("voicemail_id")})
    patients = repo.patients_by_ids(pids)
    voicemails = repo.voicemails_by_ids(vids)
    return [map_task(r, patients, voicemails) for r in rows]


def _mapped_single(repo: TasksRepo, task_id: str) -> dict[str, Any] | None:
    row = repo.get_task(task_id)
    if not row:
        return None
    patients = repo.patients_by_ids([row["patient_id"]] if row.get("patient_id") else [])
    voicemails = repo.voicemails_by_ids([row["voicemail_id"]] if row.get("voicemail_id") else [])
    return map_task(row, patients, voicemails)


# ------------------------------------------------------------- decisions ----
def apply_decision(
    repo: TasksRepo,
    task_id: str,
    decision: str,
    *,
    note: str | None = None,
    status: str | None = None,
    chw: str | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    """Returns (mapped_task, notice). mapped_task is None when the task is missing."""
    chw = chw or CHW_DEFAULT
    note = note.strip() if note and note.strip() else None
    row = repo.get_task(task_id)
    if not row:
        return None, None
    now = _now()

    if decision == "approve":
        # Idempotency: never re-run an already-completed task.
        if row.get("status") == "complete":
            return _mapped_single(repo, task_id), "Already completed — no action taken."
        notice = _execute_approval(repo, row, note, chw, now)
        return _mapped_single(repo, task_id), notice

    if decision == "reject":
        repo.update_task(task_id, {"status": "rejected", "rejected_at": now, "reviewed_at": now, "chw_note": note})
        return _mapped_single(repo, task_id), _send_denial(repo, row)

    if decision == "action_taken":
        repo.update_task(
            task_id, {"status": "complete", "approved_at": now, "approved_by": chw, "reviewed_at": now, "chw_note": note}
        )
        return _mapped_single(repo, task_id), None

    if decision == "mark_done":
        repo.update_task(task_id, {"status": "complete", "approved_at": now, "approved_by": chw})
        return _mapped_single(repo, task_id), None

    if decision == "reopen":
        new_status = status if status in REOPEN_STATUSES else "pending_approval"
        repo.update_task(
            task_id,
            {"status": new_status, "approved_at": None, "approved_by": None, "rejected_at": None, "reviewed_at": None, "chw_note": None},
        )
        return _mapped_single(repo, task_id), None

    raise ValueError(f"invalid decision: {decision}")


# ------------------------------------------------ the unified executor ----
def _execute_approval(repo: TasksRepo, row: dict[str, Any], note: str | None, chw: str, now: str) -> str | None:
    pa = row.get("proposed_action") or {}
    ptype = pa.get("type")
    task_id = row["id"]
    patient = repo.get_patient(row.get("patient_id")) or {}

    if ptype == "prescription_refill":
        from prescription_fulfillment.repo import SupabasePrescriptionFulfillmentRepo
        from prescription_fulfillment.service import fill_prescription

        result = fill_prescription(
            patient_id=row["patient_id"],
            first_name=patient.get("first_name", ""),
            last_name=patient.get("last_name", ""),
            dob=patient.get("date_of_birth", ""),
            medication_name=pa.get("medication_name", ""),
            dosage=pa.get("dosage", ""),
            instructions=pa.get("instructions", ""),
            provider_id=pa.get("provider_id", ""),
            task_id=task_id,
            repo=SupabasePrescriptionFulfillmentRepo(),
        )
        notice = _confirm("prescription_refill", result)

    elif ptype == "reschedule":
        from scheduler.repo import SupabaseSchedulerRepo
        from scheduler.service import book_appointment

        start = datetime.fromisoformat(pa["new_start"])
        end = datetime.fromisoformat(pa.get("new_end") or pa["new_start"])
        result = book_appointment(
            patient_id=row["patient_id"],
            first_name=patient.get("first_name", ""),
            last_name=patient.get("last_name", ""),
            dob=patient.get("date_of_birth", ""),
            provider_id=pa.get("provider_id", ""),
            start_time=start,
            end_time=end,
            cancel_appointment_id=pa.get("cancel_appointment_id"),
            task_id=task_id,
            repo=SupabaseSchedulerRepo(),
        )
        notice = _confirm("reschedule", result)

    elif ptype == "message_relay":
        delivered = bool(pa.get("provider_id"))
        repo.insert_message(
            task_id=task_id,
            patient_id=row.get("patient_id"),
            provider_id=pa.get("provider_id"),
            message_body=pa.get("message", ""),
            delivered=delivered,
        )
        repo.update_task(
            task_id, {"status": "complete", "approved_at": now, "approved_by": chw, "reviewed_at": now, "chw_note": note}
        )
        return "Relayed to the provider inbox." if delivered else "Saved to inbox — no provider on file, route manually."

    else:
        # Iffy/escalate-stub override: nothing executable, just complete it.
        repo.update_task(
            task_id, {"status": "complete", "approved_at": now, "approved_by": chw, "reviewed_at": now, "chw_note": note}
        )
        return "Marked complete (manual override — no automated action)."

    # refill/reschedule services already set status=complete + approved_at; add audit.
    repo.update_task(task_id, {"approved_by": chw, "reviewed_at": now, "chw_note": note})
    return notice


def _confirm(task_type: str, result: dict[str, Any]) -> str:
    """Patient confirmation SMS for a successful refill/reschedule (best-effort)."""
    from confirmation.errors import ConfirmationError
    from confirmation.service import send_confirmation

    if not result.get("success"):
        return f"Action failed — {result.get('message', 'unknown error')}"
    phone = (result.get("patient") or {}).get("phone")
    if not phone:
        return "Done — patient not texted (no phone on file)."
    try:
        sent = send_confirmation(task_type=task_type, phone_number=phone, result=result)
    except ConfirmationError as exc:
        return f"Done — patient not texted ({exc})."
    return "Patient texted a confirmation." if sent is not None else "Done — no confirmation sent."


def _send_denial(repo: TasksRepo, row: dict[str, Any]) -> str:
    """Auto denial SMS on reject; falls back to manual follow-up if it can't send."""
    from confirmation.errors import ConfirmationError
    from confirmation.service import send_denial_notice

    task_type = row.get("task_type")
    if task_type not in ("prescription_refill", "reschedule"):
        return "Rejected — follow up manually (no auto-text for this type)."
    patient = repo.get_patient(row.get("patient_id")) or {}
    phone = patient.get("phone")
    if not phone:
        return "Rejected — no phone on file, follow up manually."
    try:
        sent = send_denial_notice(task_type=task_type, phone_number=phone, first_name=patient.get("first_name"))
    except ConfirmationError as exc:
        return f"Rejected — couldn't text patient ({exc}); follow up manually."
    return "Rejected — patient texted to call back." if sent is not None else "Rejected — follow up manually."
