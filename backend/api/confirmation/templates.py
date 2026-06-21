from __future__ import annotations

from datetime import datetime
from typing import Any

# Confirmation texts only go out for the two fully-automatable actions. A
# message_relay (or anything else) returns None — no text, the doctor's
# message itself isn't something we confirm by SMS.
CONFIRMABLE_TASK_TYPES = {"prescription_refill", "reschedule"}

# Demo-only: we don't track which pharmacy a patient uses, so every refill
# names the same placeholder pharmacy.
PHARMACY_NAME = "CVS Pharmacy"


def build_confirmation_message(task_type: str, result: dict[str, Any]) -> str | None:
    if task_type not in CONFIRMABLE_TASK_TYPES:
        return None

    patient = result.get("patient") or {}
    first_name = patient.get("first_name", "there")

    if task_type == "prescription_refill":
        prescription = result.get("prescription") or {}
        medication = prescription.get("medication_name", "your medication")
        dosage = prescription.get("dosage", "")
        return (
            f"Hello, {first_name}. Your prescription refill request for {dosage} {medication} "
            f"has been approved and sent to {PHARMACY_NAME}."
        )

    appointment = result.get("appointment") or {}
    start_time = appointment.get("start_time")
    when = _format_when(start_time) if start_time else "your new time"
    provider_name = appointment.get("provider_name")
    with_doctor = f" with {provider_name}" if provider_name else ""
    return f"Hi {first_name}, your appointment has been rescheduled to {when}{with_doctor}. See you then!"


DENIAL_NOUNS = {
    "prescription_refill": "prescription refill request",
    "reschedule": "appointment request",
}


def build_denial_message(task_type: str, first_name: str | None) -> str | None:
    """The symmetric counterpart to build_confirmation_message -- sent when an
    eligibility check escalates a refill/reschedule instead of approving it.
    Deliberately generic: it doesn't repeat the specific reason (insurance,
    visit history, etc.) over SMS, just tells the patient to call back.
    """
    noun = DENIAL_NOUNS.get(task_type)
    if noun is None:
        return None

    name = first_name or "there"
    return f"Hi {name}, we're unable to process your {noun} automatically. Please call our office back so we can assist you."


def _format_when(start_time: str) -> str:
    try:
        parsed = datetime.fromisoformat(start_time)
    except ValueError:
        return start_time
    return parsed.strftime("%A, %B %-d at %-I:%M %p")
