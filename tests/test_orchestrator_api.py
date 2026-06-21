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

    def find_patient(self, first_name: str, last_name: str, dob: str) -> dict[str, Any] | None:
        return self.patient

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

    _patch_orchestrator_repo(monkeypatch)
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
