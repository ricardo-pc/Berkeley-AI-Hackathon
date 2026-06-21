from __future__ import annotations

from datetime import datetime
from typing import Any

from .repo import SchedulerRepo


def book_appointment(
    *,
    patient_id: str,
    first_name: str,
    last_name: str,
    dob: str,
    provider_id: str,
    start_time: datetime,
    end_time: datetime,
    repo: SchedulerRepo,
    cancel_appointment_id: str | None = None,
    visit_type: str = "follow_up",
) -> dict[str, Any]:
    """Write a pre-approved slot to the calendar and return a confirmation payload.

    The slot is assumed to already be validated upstream (the eligibility step),
    so this only resolves the patient, marks the old appointment rescheduled,
    and inserts the new one. patient_id is the canonical lookup key; first/last/dob
    are carried for output and human review.
    """
    patient = repo.get_patient(patient_id)
    if patient is None:
        return {
            "success": False,
            "error": "patient_not_found",
            "message": f"No patient found with id {patient_id}.",
            "patient": {
                "id": patient_id,
                "first_name": first_name,
                "last_name": last_name,
                "dob": dob,
            },
        }

    rescheduled_from = None
    if cancel_appointment_id:
        if repo.mark_appointment_rescheduled(cancel_appointment_id):
            rescheduled_from = cancel_appointment_id

    appointment = repo.insert_appointment(
        patient_id=patient["id"],
        provider_id=provider_id,
        start_time=start_time,
        end_time=end_time,
        visit_type=visit_type,
    )
    provider = repo.get_provider(provider_id)

    return {
        "success": True,
        "message": (
            f"Booked {first_name} {last_name} with provider {provider_id} "
            f"from {start_time.isoformat()} to {end_time.isoformat()}."
        ),
        "patient": {
            "id": patient["id"],
            "first_name": patient.get("first_name", first_name),
            "last_name": patient.get("last_name", last_name),
            "dob": patient.get("date_of_birth", dob),
            "phone": patient.get("phone"),
        },
        "rescheduled_from": rescheduled_from,
        "appointment": {
            "id": appointment.get("id"),
            "provider_id": appointment.get("provider_id", provider_id),
            "start_time": appointment.get("start_time", start_time.isoformat()),
            "end_time": appointment.get("end_time", end_time.isoformat()),
            "visit_type": appointment.get("visit_type", visit_type),
            "status": appointment.get("status", "scheduled"),
            "provider_name": (provider or {}).get("name"),
        },
    }
