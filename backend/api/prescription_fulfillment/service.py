from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .repo import PrescriptionFulfillmentRepo


def fill_prescription(
    *,
    patient_id: str,
    first_name: str,
    last_name: str,
    dob: str,
    medication_name: str,
    dosage: str,
    instructions: str,
    provider_id: str,
    repo: PrescriptionFulfillmentRepo,
    task_id: str | None = None,
) -> dict[str, Any]:
    """Write a pre-approved refill to the prescriptions table and return a confirmation payload.

    The refill is assumed to already be validated upstream (the eligibility step),
    so this only resolves the patient and inserts the new prescription row.
    patient_id is the canonical lookup key; first/last/dob are carried for output
    and human review.
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

    prescription = repo.insert_prescription(
        patient_id=patient["id"],
        provider_id=provider_id,
        medication_name=medication_name,
        dosage=dosage,
        instructions=instructions,
    )

    if task_id:
        repo.update_task(task_id, {"status": "complete", "approved_at": datetime.now(timezone.utc).isoformat()})

    return {
        "success": True,
        "message": f"Refilled {medication_name} ({dosage}) for {first_name} {last_name}.",
        "patient": {
            "id": patient["id"],
            "first_name": patient.get("first_name", first_name),
            "last_name": patient.get("last_name", last_name),
            "dob": patient.get("date_of_birth", dob),
            "phone": patient.get("phone"),
        },
        "prescription": {
            "id": prescription.get("id"),
            "provider_id": prescription.get("provider_id", provider_id),
            "medication_name": prescription.get("medication_name", medication_name),
            "dosage": prescription.get("dosage", dosage),
            "instructions": prescription.get("instructions", instructions),
            "active": prescription.get("active", True),
        },
    }
