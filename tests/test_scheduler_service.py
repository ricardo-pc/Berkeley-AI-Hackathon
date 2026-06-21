from __future__ import annotations

from datetime import datetime
from typing import Any

from scheduler.service import book_appointment


class FakeRepo:
    def __init__(
        self,
        patient: dict[str, Any] | None,
        provider: dict[str, Any] | None = None,
        inserted_appointment: dict[str, Any] | None = None,
    ):
        self._patient = patient
        self._provider = provider
        self._inserted_appointment = inserted_appointment or {}
        self.rescheduled_ids: list[str] = []

    def get_patient(self, patient_id: str) -> dict[str, Any] | None:
        return self._patient

    def find_patient(self, first_name: str, last_name: str, dob: str) -> dict[str, Any] | None:
        return self._patient

    def get_provider(self, provider_id: str) -> dict[str, Any] | None:
        return self._provider

    def mark_appointment_rescheduled(self, appointment_id: str) -> bool:
        self.rescheduled_ids.append(appointment_id)
        return True

    def insert_appointment(self, *, patient_id, provider_id, start_time, end_time, visit_type) -> dict[str, Any]:
        return {
            **self._inserted_appointment,
            "id": "appt-1",
            "patient_id": patient_id,
            "provider_id": provider_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "visit_type": visit_type,
            "status": "scheduled",
        }


def test_successful_booking_includes_provider_name():
    repo = FakeRepo(
        patient={"id": "pat1", "first_name": "Robert", "last_name": "Martinez", "date_of_birth": "1952-01-30", "phone": "415-555-0174"},
        provider={"id": "prov1", "name": "Dr. Sarah Lee"},
    )

    result = book_appointment(
        patient_id="pat1",
        first_name="Robert",
        last_name="Martinez",
        dob="1952-01-30",
        provider_id="prov1",
        start_time=datetime.fromisoformat("2026-06-25T09:00:00+00:00"),
        end_time=datetime.fromisoformat("2026-06-25T09:30:00+00:00"),
        repo=repo,
    )

    assert result["success"] is True
    assert result["appointment"]["provider_name"] == "Dr. Sarah Lee"
    assert result["patient"]["phone"] == "415-555-0174"


def test_missing_provider_still_succeeds_without_a_name():
    repo = FakeRepo(
        patient={"id": "pat1", "first_name": "Robert", "last_name": "Martinez", "date_of_birth": "1952-01-30"},
        provider=None,
    )

    result = book_appointment(
        patient_id="pat1",
        first_name="Robert",
        last_name="Martinez",
        dob="1952-01-30",
        provider_id="prov1",
        start_time=datetime.fromisoformat("2026-06-25T09:00:00+00:00"),
        end_time=datetime.fromisoformat("2026-06-25T09:30:00+00:00"),
        repo=repo,
    )

    assert result["success"] is True
    assert result["appointment"]["provider_name"] is None


def test_missing_patient_fails_without_booking():
    repo = FakeRepo(patient=None)

    result = book_appointment(
        patient_id="missing",
        first_name="Ghost",
        last_name="Patient",
        dob="2000-01-01",
        provider_id="prov1",
        start_time=datetime.fromisoformat("2026-06-25T09:00:00+00:00"),
        end_time=datetime.fromisoformat("2026-06-25T09:30:00+00:00"),
        repo=repo,
    )

    assert result["success"] is False
    assert result["error"] == "patient_not_found"
