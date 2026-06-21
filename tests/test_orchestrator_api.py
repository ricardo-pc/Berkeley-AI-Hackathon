from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi.testclient import TestClient

from backend.orchestrator import main as orchestrator_main


def _intake_payload(request_type: str = "refill") -> dict[str, Any]:
    request = {
        "type": request_type,
        "details": "Refill for Lisinopril 10 milligrams once daily with food",
        "orders": ["Lisinopril"],
        "preferred_times": [],
        "urgency_signal": "routine",
    }
    if request_type == "reschedule":
        request = {
            "type": "reschedule",
            "details": "Move appointment to June 24th at 3 PM",
            "orders": [],
            "preferred_times": [
                {
                    "raw_text": "June 24th at 3 PM",
                    "date": "2026-06-24",
                    "start_time": "15:00",
                    "time_of_day": "afternoon",
                }
            ],
            "urgency_signal": "routine",
        }
    if request_type == "message_relay":
        request = {
            "type": "message_relay",
            "details": "Caller reports dizziness after starting Sertraline.",
            "orders": [],
            "preferred_times": [],
            "urgency_signal": "urgent",
        }
    return {
        "first_name": "Maria",
        "last_name": "Gonzalez",
        "date_of_birth": "1978-03-12",
        "phone_number": "415-555-0101",
        "insurance_plan": "Blue Cross PPO",
        "request": request,
        "requests": [request],
        "missing_fields": [],
        "transcript": "Maria Gonzalez needs help.\nPlease call back.",
    }


class FakeOrchestratorRepo:
    patient: dict[str, Any] | None = {
        "id": "patient-1",
        "first_name": "Maria",
        "last_name": "Gonzalez",
        "date_of_birth": "1978-03-12",
        "insurance_plan": "Blue Cross PPO",
        "insurance_valid": True,
        "preferred_provider_id": "provider-1",
    }
    appointment: dict[str, Any] | None = {"id": "appointment-1"}
    duplicate_task: dict[str, Any] | None = None
    inserted_tasks: list[dict[str, Any]]

    def __init__(self) -> None:
        self.inserted_tasks = []
        self.duplicate_task = None

    def find_patient(self, first_name: str, last_name: str, dob: str) -> dict[str, Any] | None:
        return self.patient

    def insert_task(self, fields: dict[str, Any]) -> dict[str, Any]:
        row = {"id": f"inserted-task-{len(self.inserted_tasks) + 1}", **fields}
        self.inserted_tasks.append(row)
        return row

    def find_duplicate_task(self, fields: dict[str, Any]) -> dict[str, Any] | None:
        if self.duplicate_task and self.duplicate_task.get("status") in orchestrator_main.REVIEW_QUEUE_STATUSES:
            return self.duplicate_task
        return None

    def get_next_scheduled_appointment(self, patient_id: str) -> dict[str, Any] | None:
        return self.appointment


def _patch_orchestrator_repo(monkeypatch, repo: FakeOrchestratorRepo | None = None) -> FakeOrchestratorRepo:
    fake_repo = repo or FakeOrchestratorRepo()
    monkeypatch.setattr(orchestrator_main, "OrchestratorRepo", lambda: fake_repo)
    return fake_repo


def test_refill_accepts_intake_and_calls_prescription_eligibility(monkeypatch):
    seen = {}

    def fake_run_prescription_eligibility_check(**kwargs):
        seen.update(kwargs)
        return {"eligible": True, "status": "pending_approval", "checks": {"prescription": {"eligible": True}}}

    _patch_orchestrator_repo(monkeypatch)
    monkeypatch.setattr(orchestrator_main, "SupabasePrescriptionEligibilityRepo", lambda: object())
    monkeypatch.setattr(orchestrator_main, "run_prescription_eligibility_check", fake_run_prescription_eligibility_check)

    response = TestClient(orchestrator_main.app).post("/api/refill", json={"intake": _intake_payload()})

    assert response.status_code == 200
    assert response.json()["eligible"] is True
    assert seen["patient_id"] == "patient-1"
    assert seen["medication_name"] == "Lisinopril"
    assert seen["dosage"] == "10mg"
    assert seen["instructions"] == "once daily with food"


def test_reschedule_derives_provider_and_times_from_intake(monkeypatch):
    seen = {}

    def fake_run_schedule_eligibility_check(**kwargs):
        seen.update(kwargs)
        return {"eligible": True, "status": "pending_approval", "checks": {"scheduling_eligibility": {}}}

    repo = _patch_orchestrator_repo(monkeypatch)
    monkeypatch.setattr(orchestrator_main, "SupabaseScheduleEligibilityRepo", lambda: object())
    monkeypatch.setattr(orchestrator_main, "run_schedule_eligibility_check", fake_run_schedule_eligibility_check)

    response = TestClient(orchestrator_main.app).post(
        "/api/reschedule",
        json={"intake": _intake_payload("reschedule"), "task_id": "task-1"},
    )

    assert response.status_code == 200
    assert seen["patient_id"] == "patient-1"
    assert seen["provider_id"] == "provider-1"
    assert seen["requested_start"] == datetime.fromisoformat("2026-06-24T15:00:00+00:00")
    assert seen["requested_end"] == datetime.fromisoformat("2026-06-24T15:30:00+00:00")
    assert seen["cancel_appointment_id"] == "appointment-1"
    assert seen["task_id"] == "task-1"
    assert repo.inserted_tasks == []


def test_fresh_reschedule_inserts_new_task_and_returns_task_id(monkeypatch):
    def fake_run_schedule_eligibility_check(**kwargs):
        return {
            "eligible": True,
            "status": "pending_approval",
            "checks": {"scheduling_eligibility": {"conflict": False}},
            "proposed_action": {"type": "reschedule", "new_start": "2026-06-24T15:00:00+00:00"},
        }

    repo = _patch_orchestrator_repo(monkeypatch)
    monkeypatch.setattr(orchestrator_main, "SupabaseScheduleEligibilityRepo", lambda: object())
    monkeypatch.setattr(orchestrator_main, "run_schedule_eligibility_check", fake_run_schedule_eligibility_check)

    response = TestClient(orchestrator_main.app).post("/api/reschedule", json={"intake": _intake_payload("reschedule")})

    assert response.status_code == 200
    assert response.json()["task_id"] == "inserted-task-1"
    assert len(repo.inserted_tasks) == 1
    assert repo.inserted_tasks[0]["task_type"] == "reschedule"
    assert repo.inserted_tasks[0]["status"] == "pending_approval"
    assert repo.inserted_tasks[0]["agent_checks"]["scheduling_eligibility"]["conflict"] is False


def test_fresh_refill_reuses_matching_existing_review_task(monkeypatch):
    def fake_run_prescription_eligibility_check(**kwargs):
        return {
            "eligible": True,
            "status": "pending_approval",
            "checks": {"prescription": {"eligible": True}},
            "proposed_action": {
                "type": "prescription_refill",
                "medication_name": "Lisinopril",
                "dosage": "10mg",
                "instructions": "once daily with food",
                "provider_id": "provider-1",
                "patient_id": "patient-1",
            },
        }

    repo = _patch_orchestrator_repo(monkeypatch)
    repo.duplicate_task = {
        "id": "existing-task-1",
        "patient_id": "patient-1",
        "task_type": "prescription_refill",
        "status": "pending_approval",
        "agent_checks": {"prescription": {"eligible": True}},
        "proposed_action": {
            "type": "prescription_refill",
            "medication_name": "Lisinopril",
            "dosage": "10mg",
            "instructions": "once daily with food",
            "provider_id": "provider-1",
            "patient_id": "patient-1",
        },
        "flagged_reason": None,
    }
    monkeypatch.setattr(orchestrator_main, "SupabasePrescriptionEligibilityRepo", lambda: object())
    monkeypatch.setattr(orchestrator_main, "run_prescription_eligibility_check", fake_run_prescription_eligibility_check)

    response = TestClient(orchestrator_main.app).post("/api/refill", json={"intake": _intake_payload()})

    assert response.status_code == 200
    assert response.json()["task_id"] == "existing-task-1"
    assert response.json()["duplicate_task_reused"] is True
    assert repo.inserted_tasks == []


def test_completed_duplicate_does_not_block_new_review_task(monkeypatch):
    def fake_run_prescription_eligibility_check(**kwargs):
        return {
            "eligible": True,
            "status": "pending_approval",
            "checks": {"prescription": {"eligible": True}},
            "proposed_action": {
                "type": "prescription_refill",
                "medication_name": "Lisinopril",
                "dosage": "10mg",
                "instructions": "once daily with food",
                "provider_id": "provider-1",
                "patient_id": "patient-1",
            },
        }

    repo = _patch_orchestrator_repo(monkeypatch)
    repo.duplicate_task = {
        "id": "completed-task-1",
        "patient_id": "patient-1",
        "task_type": "prescription_refill",
        "status": "complete",
        "agent_checks": {"prescription": {"eligible": True}},
        "proposed_action": {
            "type": "prescription_refill",
            "medication_name": "Lisinopril",
            "dosage": "10mg",
            "instructions": "once daily with food",
            "provider_id": "provider-1",
            "patient_id": "patient-1",
        },
        "flagged_reason": None,
    }
    monkeypatch.setattr(orchestrator_main, "SupabasePrescriptionEligibilityRepo", lambda: object())
    monkeypatch.setattr(orchestrator_main, "run_prescription_eligibility_check", fake_run_prescription_eligibility_check)

    response = TestClient(orchestrator_main.app).post("/api/refill", json={"intake": _intake_payload()})

    assert response.status_code == 200
    assert response.json()["task_id"] == "inserted-task-1"
    assert "duplicate_task_reused" not in response.json()
    assert len(repo.inserted_tasks) == 1


def test_conflict_with_alternative_inserts_pending_manual_review_task(monkeypatch):
    def fake_run_schedule_eligibility_check(**kwargs):
        return {
            "eligible": False,
            "status": "pending_approval",
            "flagged_reason": None,
            "checks": {
                "scheduling_eligibility": {
                    "conflict": True,
                    "conflict_reason": "Requested time overlaps an existing appointment.",
                    "alternative_slot_found": True,
                }
            },
            "proposed_action": {
                "type": "reschedule",
                "new_start": "2026-06-24T15:30:00+00:00",
                "new_end": "2026-06-24T16:00:00+00:00",
            },
        }

    repo = _patch_orchestrator_repo(monkeypatch)
    monkeypatch.setattr(orchestrator_main, "SupabaseScheduleEligibilityRepo", lambda: object())
    monkeypatch.setattr(orchestrator_main, "run_schedule_eligibility_check", fake_run_schedule_eligibility_check)

    response = TestClient(orchestrator_main.app).post("/api/reschedule", json={"intake": _intake_payload("reschedule")})

    assert response.status_code == 200
    assert response.json()["status"] == "pending_approval"
    assert response.json()["task_id"] == "inserted-task-1"
    assert repo.inserted_tasks[0]["status"] == "pending_approval"
    assert repo.inserted_tasks[0]["agent_checks"]["scheduling_eligibility"]["conflict"] is True
    assert repo.inserted_tasks[0]["proposed_action"]["type"] == "reschedule"


def test_message_relay_accepts_intake_and_calls_message_relay(monkeypatch):
    seen = {}

    def fake_run_message_relay_check(**kwargs):
        seen.update(kwargs)
        return {"worth_relaying": True, "status": "pending_approval"}

    _patch_orchestrator_repo(monkeypatch)
    monkeypatch.setattr(orchestrator_main, "SupabaseMessageRelayRepo", lambda: object())
    monkeypatch.setattr(orchestrator_main, "run_message_relay_check", fake_run_message_relay_check)

    response = TestClient(orchestrator_main.app).post("/api/message-relay", json={"intake": _intake_payload("message_relay")})

    assert response.status_code == 200
    assert response.json()["worth_relaying"] is True
    assert seen["patient_id"] == "patient-1"
    assert seen["message"] == "Caller reports dizziness after starting Sertraline."


def test_wrong_request_type_returns_400(monkeypatch):
    _patch_orchestrator_repo(monkeypatch)

    response = TestClient(orchestrator_main.app).post("/api/refill", json={"intake": _intake_payload("reschedule")})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "wrong_request_type"


def test_missing_identity_returns_400():
    intake = _intake_payload()
    intake["date_of_birth"] = None

    response = TestClient(orchestrator_main.app).post("/api/refill", json={"intake": intake})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "missing_patient_identity"


def test_unknown_patient_returns_404(monkeypatch):
    _patch_orchestrator_repo(monkeypatch, FakeOrchestratorRepo())
    orchestrator_main.OrchestratorRepo().patient = None

    response = TestClient(orchestrator_main.app).post("/api/refill", json={"intake": _intake_payload()})

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "patient_not_found"


def test_invalid_insurance_short_circuits_before_type_specific_check(monkeypatch):
    repo = FakeOrchestratorRepo()
    repo.patient = {
        **(repo.patient or {}),
        "insurance_valid": False,
        "insurance_plan": "Kaiser Permanente",
    }
    _patch_orchestrator_repo(monkeypatch, repo)

    def fail_if_called(**kwargs):
        raise AssertionError("type-specific eligibility should not be called")

    monkeypatch.setattr(orchestrator_main, "run_prescription_eligibility_check", fail_if_called)

    response = TestClient(orchestrator_main.app).post("/api/refill", json={"intake": _intake_payload()})

    assert response.status_code == 200
    assert response.json()["status"] == "escalated"
    assert response.json()["checks"]["insurance"]["valid"] is False
