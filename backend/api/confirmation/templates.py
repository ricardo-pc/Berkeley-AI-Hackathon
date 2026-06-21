from __future__ import annotations

from datetime import datetime
from typing import Any

# Confirmation texts only go out for the two fully-automatable actions. A
# message_relay (or anything else) returns None — no text, the doctor's
# message itself isn't something we confirm by SMS.
CONFIRMABLE_TASK_TYPES = {"prescription_refill", "reschedule"}


def build_confirmation_message(task_type: str, result: dict[str, Any]) -> str | None:
    if task_type not in CONFIRMABLE_TASK_TYPES:
        return None

    patient = result.get("patient") or {}
    first_name = patient.get("first_name", "there")

    if task_type == "prescription_refill":
        prescription = result.get("prescription") or {}
        medication = prescription.get("medication_name", "your medication")
        dosage = prescription.get("dosage", "")
        instructions = prescription.get("instructions", "")
        message = f"Hi {first_name}, your {medication} {dosage} refill has been approved and will be ready for pickup."
        if instructions:
            message += f" Instructions: {instructions}."
        return message

    appointment = result.get("appointment") or {}
    start_time = appointment.get("start_time")
    when = _format_when(start_time) if start_time else "your new time"
    return f"Hi {first_name}, your appointment has been rescheduled to {when}. See you then!"


def _format_when(start_time: str) -> str:
    try:
        parsed = datetime.fromisoformat(start_time)
    except ValueError:
        return start_time
    return parsed.strftime("%A, %B %-d at %-I:%M %p")
