from __future__ import annotations

import re
from typing import Any, Callable

from .classifier import classify_message
from .errors import PatientNotFoundError
from .repo import MessageRelayRepo

_TITLES = {"dr", "doctor", "md", "do", "mr", "mrs", "ms", "miss"}


def run_message_relay_check(
    *,
    patient_id: str,
    message: str,
    repo: MessageRelayRepo,
    first_name: str | None = None,
    last_name: str | None = None,
    dob: str | None = None,
    task_id: str | None = None,
    classify: Callable[[str], dict[str, Any]] = classify_message,
) -> dict[str, Any]:
    patient = repo.get_patient(patient_id)
    if not patient:
        raise PatientNotFoundError(patient_id)

    decision = classify(message)
    route = decision.get("route", "none")
    category = decision.get("category")
    draft = (decision.get("draft_message") or "").strip() or None
    mentioned_doctor = (decision.get("mentioned_doctor") or "").strip() or None
    reasoning = decision.get("reasoning", "")

    worth_relaying = route in ("physician", "staff")

    # Resolve the patient's doctor on file (preferred_provider_id).
    provider_id = patient.get("preferred_provider_id")
    doctor_on_file = None
    if provider_id:
        provider = repo.get_provider(provider_id)
        doctor_on_file = provider.get("name")

    # Name-match check: relay still proceeds, but flag a mismatch for the human.
    doctor_matches: bool | None = None
    if mentioned_doctor and doctor_on_file:
        doctor_matches = _names_match(mentioned_doctor, doctor_on_file)

    flags: list[str] = []
    if worth_relaying and not provider_id:
        flags.append("patient has no preferred provider on file; cannot determine recipient doctor")
    if doctor_matches is False:
        flags.append(
            f"message names \"{mentioned_doctor}\" but patient's doctor on file is \"{doctor_on_file}\""
        )
    flagged_reason = "; ".join(flags) if flags else None

    status = "pending_approval" if worth_relaying else "rejected"

    proposed_action = None
    if worth_relaying:
        proposed_action = {
            "type": "message_relay",
            "assignee": route,  # "physician" or "staff"
            "patient_id": patient_id,
            "provider_id": provider_id,
            "message": draft,
        }

    agent_checks = {
        "message_relay": {
            "route": route,
            "category": category,
            "draft_message": draft,
            "mentioned_doctor": mentioned_doctor,
            "doctor_on_file": doctor_on_file,
            "doctor_matches": doctor_matches,
            "reasoning": reasoning,
        }
    }

    result = {
        "patient": {
            "id": patient_id,
            "first_name": patient.get("first_name", first_name),
            "last_name": patient.get("last_name", last_name),
            "dob": patient.get("date_of_birth", dob),
        },
        "worth_relaying": worth_relaying,
        "route": route,
        "status": status,
        "agent_summary": reasoning,
        "agent_checks": agent_checks,
        "flagged_reason": flagged_reason,
        "proposed_action": proposed_action,
    }

    if task_id:
        existing_task = repo.get_task(task_id)
        merged_checks = {**(existing_task.get("agent_checks") or {}), **agent_checks}
        repo.update_task(
            task_id,
            {
                "status": status,
                "agent_summary": reasoning,
                "agent_checks": merged_checks,
                "proposed_action": proposed_action,
                "flagged_reason": flagged_reason,
            },
        )

    return result


def _names_match(mentioned: str, on_file: str) -> bool:
    """Loose match: do the meaningful name tokens overlap (ignoring titles)?"""
    return bool(_name_tokens(mentioned) & _name_tokens(on_file))


def _name_tokens(name: str) -> set[str]:
    tokens = re.findall(r"[a-z]+", name.lower())
    return {t for t in tokens if t not in _TITLES and len(t) > 1}
