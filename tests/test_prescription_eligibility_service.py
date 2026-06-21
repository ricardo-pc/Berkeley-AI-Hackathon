from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest

from prescription_eligibility.errors import PatientNotFoundError
from prescription_eligibility.service import run_prescription_eligibility_check

NOW = datetime.fromisoformat("2026-06-20T00:00:00+00:00")


class FakeRepo:
    def __init__(
        self,
        patient: dict[str, Any] | None,
        appointments: list[dict[str, Any]] | None = None,
        prescriptions: list[dict[str, Any]] | None = None,
        existing_task: dict[str, Any] | None = None,
    ):
        self._patient = patient
        self._appointments = appointments or []
        self._prescriptions = prescriptions or []
        self._existing_task = existing_task or {}
        self.updated_tasks: list[tuple[str, dict[str, Any]]] = []

    def get_patient(self, patient_id: str) -> dict[str, Any]:
        return self._patient or {}

    def get_appointments(self, patient_id: str) -> list[dict[str, Any]]:
        return self._appointments

    def get_prescriptions(self, patient_id: str) -> list[dict[str, Any]]:
        return self._prescriptions

    def get_task(self, task_id: str) -> dict[str, Any]:
        return self._existing_task

    def update_task(self, task_id: str, fields: dict[str, Any]) -> None:
        self.updated_tasks.append((task_id, fields))


def test_eligible_refill_still_surfaces_a_conflict_warning():
    """Mirrors Maria Gonzalez's seeded scenario: eligible, but flagged for physician review."""
    repo = FakeRepo(
        patient={"id": "pat1", "date_of_birth": "1978-03-12"},
        appointments=[
            {"status": "scheduled", "start_time": "2026-01-10T10:00:00+00:00"},
            {"status": "scheduled", "start_time": "2026-09-15T10:00:00+00:00"},
        ],
        prescriptions=[
            {
                "medication_name": "Lisinopril",
                "dosage": "10mg",
                "instructions": "once daily with food",
                "active": True,
                "provider_id": "prov1",
            },
            {"medication_name": "Amlodipine", "dosage": "5mg", "instructions": "once daily", "active": True},
        ],
    )

    result = run_prescription_eligibility_check(
        patient_id="pat1",
        medication_name="Lisinopril",
        dosage="10mg",
        instructions="once daily with food",
        repo=repo,
        now=NOW,
    )

    assert result["eligible"] is True
    assert result["status"] == "pending_approval"
    assert result["flagged_reason"] is None
    assert "agent_checks" not in result
    assert "agent_summary" not in result
    assert result["checks"]["prescription"]["eligible"] is True
    assert result["checks"]["prescription"]["conflict"] is True
    assert result["checks"]["prescription"]["conflict_medication"] == "Amlodipine"
    assert result["proposed_action"] == {
        "type": "prescription_refill",
        "medication_name": "Lisinopril",
        "dosage": "10mg",
        "instructions": "once daily with food",
        "provider_id": "prov1",
        "patient_id": "pat1",
    }


def test_visit_too_long_ago_escalates_without_a_proposed_action():
    """Mirrors James Okafor's seeded scenario: last visit outside the window."""
    repo = FakeRepo(
        patient={"id": "pat2", "date_of_birth": "1965-07-24"},
        appointments=[{"status": "scheduled", "start_time": "2024-11-20T09:00:00+00:00"}],
        prescriptions=[
            {
                "medication_name": "Metformin",
                "dosage": "500mg",
                "instructions": "twice daily with meals",
                "active": True,
                "provider_id": "prov2",
            },
        ],
    )

    result = run_prescription_eligibility_check(
        patient_id="pat2",
        medication_name="Metformin",
        dosage="500mg",
        instructions="twice daily with meals",
        repo=repo,
        now=NOW,
    )

    assert result["eligible"] is False
    assert result["status"] == "escalated"
    assert "recent-visit window" in result["flagged_reason"]
    assert result["proposed_action"] is None


def test_never_prescribed_before_escalates():
    repo = FakeRepo(
        patient={"id": "pat3", "date_of_birth": "1990-01-01"},
        appointments=[
            {"status": "scheduled", "start_time": "2026-01-10T10:00:00+00:00"},
            {"status": "scheduled", "start_time": "2026-09-15T10:00:00+00:00"},
        ],
        prescriptions=[],
    )

    result = run_prescription_eligibility_check(
        patient_id="pat3",
        medication_name="Atorvastatin",
        dosage="20mg",
        instructions="once daily at bedtime",
        repo=repo,
        now=NOW,
    )

    assert result["eligible"] is False
    assert result["status"] == "escalated"
    assert "not been prescribed" in result["flagged_reason"]
    assert result["proposed_action"] is None


def test_task_id_writes_the_result_back_and_merges_existing_checks():
    repo = FakeRepo(
        patient={"id": "pat1", "date_of_birth": "1978-03-12"},
        appointments=[
            {"status": "scheduled", "start_time": "2026-01-10T10:00:00+00:00"},
            {"status": "scheduled", "start_time": "2026-09-15T10:00:00+00:00"},
        ],
        prescriptions=[
            {
                "medication_name": "Lisinopril",
                "dosage": "10mg",
                "instructions": "once daily with food",
                "active": True,
                "provider_id": "prov1",
            },
        ],
        existing_task={"agent_checks": {"insurance_eligibility": {"valid": True}}},
    )

    result = run_prescription_eligibility_check(
        patient_id="pat1",
        medication_name="Lisinopril",
        dosage="10mg",
        instructions="once daily with food",
        repo=repo,
        task_id="task-1",
        now=NOW,
    )

    assert len(repo.updated_tasks) == 1
    written_task_id, written_fields = repo.updated_tasks[0]
    assert written_task_id == "task-1"
    assert written_fields["status"] == result["status"]
    assert written_fields["agent_summary"] is None
    assert written_fields["agent_checks"]["insurance_eligibility"] == {"valid": True}
    assert "prescription" in written_fields["agent_checks"]
    assert "prescription_eligibility" not in written_fields["agent_checks"]


def test_no_task_id_does_not_touch_the_tasks_table():
    repo = FakeRepo(patient={"id": "pat1", "date_of_birth": "1978-03-12"})

    run_prescription_eligibility_check(
        patient_id="pat1",
        medication_name="Lisinopril",
        dosage="10mg",
        instructions="once daily with food",
        repo=repo,
        now=NOW,
    )

    assert repo.updated_tasks == []


def test_missing_patient_raises_a_not_found_error():
    repo = FakeRepo(patient=None)

    with pytest.raises(PatientNotFoundError):
        run_prescription_eligibility_check(
            patient_id="missing-patient",
            medication_name="Lisinopril",
            dosage="10mg",
            instructions="once daily with food",
            repo=repo,
            now=NOW,
        )
