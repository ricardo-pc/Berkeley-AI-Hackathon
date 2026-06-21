from __future__ import annotations

from datetime import datetime

from fastapi.testclient import TestClient

import main
from intake.schemas import IntakeExtraction
from transcription.schemas import TranscriptionResponse


def _intake_payload(request_type: str = "refill") -> dict:
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


class FakeSchedulerRepo:
    def find_patient(self, first_name: str, last_name: str, dob: str) -> dict:
        return {
            "id": "patient-1",
            "first_name": first_name,
            "last_name": last_name,
            "date_of_birth": dob,
        }


def test_api_intake_returns_sanitized_extraction(monkeypatch):
    def fake_run_intake_extraction(stt_json: dict):
        assert stt_json == {"transcript": "hello"}
        return IntakeExtraction(**_intake_payload())

    monkeypatch.setattr(main, "run_intake_extraction", fake_run_intake_extraction)
    client = TestClient(main.app)

    response = client.post("/api/intake", json={"stt_json": {"transcript": "hello"}})

    assert response.status_code == 200
    payload = response.json()
    assert payload["request"]["type"] == "refill"
    assert payload["transcript"] == "Maria Gonzalez needs help. Please call back."


def test_api_voicemail_intake_chains_transcription_and_intake(monkeypatch):
    async def fake_transcribe_audio(audio_bytes: bytes, filename: str | None, content_type: str | None = None):
        assert audio_bytes == b"audio"
        return TranscriptionResponse(id="tr_1", transcript="James needs a refill.\nThanks.")

    def fake_run_intake_extraction(stt_json: dict):
        assert stt_json["transcript"] == "James needs a refill.\nThanks."
        return IntakeExtraction(**_intake_payload())

    monkeypatch.setattr(main, "transcribe_audio", fake_transcribe_audio)
    monkeypatch.setattr(main, "run_intake_extraction", fake_run_intake_extraction)
    client = TestClient(main.app)

    response = client.post(
        "/api/voicemail/intake",
        files={"file": ("sample.wav", b"audio", "audio/wav")},
    )

    assert response.status_code == 200
    assert response.json()["transcript"] == "James needs a refill. Thanks."
    assert response.json()["intake"]["request"]["type"] == "refill"


def test_prescription_eligibility_accepts_intake_payload(monkeypatch):
    seen = {}

    def fake_run_prescription_eligibility_check(**kwargs):
        seen.update(kwargs)
        return {
            "eligible": True,
            "status": "pending_approval",
            "checks": {"prescription": {"eligible": True}},
        }

    monkeypatch.setattr(main, "SupabaseSchedulerRepo", lambda: FakeSchedulerRepo())
    monkeypatch.setattr(main, "SupabasePrescriptionEligibilityRepo", lambda: object())
    monkeypatch.setattr(main, "run_prescription_eligibility_check", fake_run_prescription_eligibility_check)
    client = TestClient(main.app)

    response = client.post("/api/prescription-eligibility", json={"intake": _intake_payload()})

    assert response.status_code == 200
    assert response.json()["eligible"] is True
    assert response.json()["checks"]["prescription"]["eligible"] is True
    assert "agent_checks" not in response.json()
    assert "agent_summary" not in response.json()
    assert seen["patient_id"] == "patient-1"
    assert seen["medication_name"] == "Lisinopril"
    assert seen["dosage"] == "10mg"
    assert seen["instructions"] == "once daily with food"


def test_schedule_eligibility_accepts_intake_payload_with_required_slot(monkeypatch):
    seen = {}

    def fake_run_schedule_eligibility_check(**kwargs):
        seen.update(kwargs)
        return {
            "eligible": True,
            "status": "pending_approval",
            "checks": {"scheduling_eligibility": {"conflict": False}},
        }

    monkeypatch.setattr(main, "SupabaseSchedulerRepo", lambda: FakeSchedulerRepo())
    monkeypatch.setattr(main, "SupabaseScheduleEligibilityRepo", lambda: object())
    monkeypatch.setattr(main, "run_schedule_eligibility_check", fake_run_schedule_eligibility_check)
    client = TestClient(main.app)

    response = client.post(
        "/api/schedule-eligibility",
        json={
            "intake": _intake_payload("reschedule"),
            "provider_id": "provider-1",
            "requested_start": "2026-06-24T15:00:00+00:00",
            "requested_end": "2026-06-24T15:30:00+00:00",
        },
    )

    assert response.status_code == 200
    assert response.json()["eligible"] is True
    assert response.json()["checks"]["scheduling_eligibility"]["conflict"] is False
    assert "agent_checks" not in response.json()
    assert "agent_summary" not in response.json()
    assert seen["patient_id"] == "patient-1"
    assert seen["provider_id"] == "provider-1"
    assert seen["requested_start"] == datetime.fromisoformat("2026-06-24T15:00:00+00:00")


def test_message_relay_accepts_intake_payload(monkeypatch):
    seen = {}

    def fake_run_message_relay_check(**kwargs):
        seen.update(kwargs)
        return {"worth_relaying": True, "status": "pending_approval"}

    monkeypatch.setattr(main, "SupabaseSchedulerRepo", lambda: FakeSchedulerRepo())
    monkeypatch.setattr(main, "SupabaseMessageRelayRepo", lambda: object())
    monkeypatch.setattr(main, "run_message_relay_check", fake_run_message_relay_check)
    client = TestClient(main.app)

    response = client.post("/api/message-relay", json={"intake": _intake_payload("message_relay")})

    assert response.status_code == 200
    assert response.json()["worth_relaying"] is True
    assert seen["patient_id"] == "patient-1"
    assert seen["message"] == "Caller reports dizziness after starting Sertraline."


def test_schedule_eligibility_requires_slot_fields(monkeypatch):
    monkeypatch.setattr(main, "SupabaseSchedulerRepo", lambda: FakeSchedulerRepo())
    client = TestClient(main.app)

    response = client.post("/api/schedule-eligibility", json={"intake": _intake_payload("reschedule")})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "missing_schedule_fields"


def test_prescription_eligibility_requires_order_and_dosage():
    intake = _intake_payload()
    intake["request"]["orders"] = []
    intake["requests"] = [intake["request"]]
    client = TestClient(main.app)

    response = client.post("/api/prescription-eligibility", json={"intake": intake})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "missing_prescription_order"


def test_workflow_requires_patient_identity():
    intake = _intake_payload("message_relay")
    intake["date_of_birth"] = None
    client = TestClient(main.app)

    response = client.post("/api/message-relay", json={"intake": intake})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "missing_patient_identity"
