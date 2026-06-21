from __future__ import annotations

from typing import Any

from prescription_fulfillment.service import fill_prescription


class FakeRepo:
    def __init__(self, patient: dict[str, Any] | None, inserted: dict[str, Any] | None = None):
        self._patient = patient
        self._inserted = inserted or {}
        self.insert_calls: list[dict[str, Any]] = []

    def get_patient(self, patient_id: str) -> dict[str, Any] | None:
        return self._patient

    def insert_prescription(
        self,
        *,
        patient_id: str,
        provider_id: str,
        medication_name: str,
        dosage: str,
        instructions: str,
    ) -> dict[str, Any]:
        call = {
            "patient_id": patient_id,
            "provider_id": provider_id,
            "medication_name": medication_name,
            "dosage": dosage,
            "instructions": instructions,
        }
        self.insert_calls.append(call)
        return {**call, "id": "rx-1", "active": True}


def test_successful_refill_inserts_and_returns_confirmation():
    repo = FakeRepo(patient={"id": "pat1", "first_name": "Maria", "last_name": "Gonzalez", "date_of_birth": "1978-03-12"})

    result = fill_prescription(
        patient_id="pat1",
        first_name="Maria",
        last_name="Gonzalez",
        dob="1978-03-12",
        medication_name="Lisinopril",
        dosage="10mg",
        instructions="once daily with food",
        provider_id="prov1",
        repo=repo,
    )

    assert result["success"] is True
    assert result["patient"]["id"] == "pat1"
    assert result["prescription"]["medication_name"] == "Lisinopril"
    assert result["prescription"]["id"] == "rx-1"
    assert len(repo.insert_calls) == 1
    assert repo.insert_calls[0]["patient_id"] == "pat1"


def test_missing_patient_fails_without_inserting():
    repo = FakeRepo(patient=None)

    result = fill_prescription(
        patient_id="missing-patient",
        first_name="Ghost",
        last_name="Patient",
        dob="2000-01-01",
        medication_name="Lisinopril",
        dosage="10mg",
        instructions="once daily with food",
        provider_id="prov1",
        repo=repo,
    )

    assert result["success"] is False
    assert result["error"] == "patient_not_found"
    assert repo.insert_calls == []
