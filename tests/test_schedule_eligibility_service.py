from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest

from scheduling_eligibility.errors import ProviderNotFoundError
from scheduling_eligibility.service import run_schedule_eligibility_check

PROVIDER_AVAILABILITY = {
    "mon": ["09:00", "17:00"],
    "tue": ["09:00", "17:00"],
    "wed": ["09:00", "17:00"],
    "thu": ["09:00", "17:00"],
    "fri": ["09:00", "17:00"],
}


class FakeRepo:
    def __init__(
        self,
        provider: dict[str, Any] | None,
        appointments: list[dict[str, Any]] | None = None,
        reschedule_tasks: list[dict[str, Any]] | None = None,
        existing_task: dict[str, Any] | None = None,
    ):
        self._provider = provider
        self._appointments = appointments or []
        self._reschedule_tasks = reschedule_tasks or []
        self._existing_task = existing_task or {}
        self.updated_tasks: list[tuple[str, dict[str, Any]]] = []

    def get_provider(self, provider_id: str) -> dict[str, Any]:
        return self._provider or {}

    def get_scheduled_appointments(self, provider_id: str) -> list[dict[str, Any]]:
        return self._appointments

    def get_reschedule_tasks_since_last_visit(self, patient_id: str) -> list[dict[str, Any]]:
        return self._reschedule_tasks

    def get_task(self, task_id: str) -> dict[str, Any]:
        return self._existing_task

    def update_task(self, task_id: str, fields: dict[str, Any]) -> None:
        self.updated_tasks.append((task_id, fields))


def test_open_slot_is_eligible_with_a_proposed_reschedule_action():
    repo = FakeRepo(provider={"id": "p1", "availability": PROVIDER_AVAILABILITY})

    result = run_schedule_eligibility_check(
        patient_id="pat1",
        provider_id="p1",
        requested_start=datetime.fromisoformat("2026-06-24T10:00:00+00:00"),
        requested_end=datetime.fromisoformat("2026-06-24T10:30:00+00:00"),
        repo=repo,
    )

    assert result["eligible"] is True
    assert result["status"] == "pending_approval"
    assert result["flagged_reason"] is None
    assert result["proposed_action"]["type"] == "reschedule"
    assert "agent_checks" not in result
    assert "agent_summary" not in result
    assert result["checks"]["scheduling_eligibility"]["conflict"] is False
    assert result["suggested_timeslot"] == {
        "start": "2026-06-24T10:00:00+00:00",
        "end": "2026-06-24T10:30:00+00:00",
        "provider_id": "p1",
    }


def test_eligible_slot_has_no_suggested_timeslot_field_when_conflicting():
    existing = [
        {
            "id": "other",
            "status": "scheduled",
            "start_time": "2026-06-24T10:00:00+00:00",
            "end_time": "2026-06-24T10:30:00+00:00",
        }
    ]
    repo = FakeRepo(provider={"id": "p1", "availability": PROVIDER_AVAILABILITY}, appointments=existing)

    result = run_schedule_eligibility_check(
        patient_id="pat1",
        provider_id="p1",
        requested_start=datetime.fromisoformat("2026-06-24T10:00:00+00:00"),
        requested_end=datetime.fromisoformat("2026-06-24T10:30:00+00:00"),
        repo=repo,
    )

    assert result["suggested_timeslot"] is None


def test_task_id_writes_the_result_back_to_the_tasks_table():
    repo = FakeRepo(provider={"id": "p1", "availability": PROVIDER_AVAILABILITY})

    result = run_schedule_eligibility_check(
        patient_id="pat1",
        provider_id="p1",
        requested_start=datetime.fromisoformat("2026-06-24T10:00:00+00:00"),
        requested_end=datetime.fromisoformat("2026-06-24T10:30:00+00:00"),
        repo=repo,
        task_id="task-1",
    )

    assert len(repo.updated_tasks) == 1
    written_task_id, written_fields = repo.updated_tasks[0]
    assert written_task_id == "task-1"
    assert written_fields["status"] == result["status"]
    assert written_fields["agent_summary"] is None
    assert written_fields["agent_checks"] == result["checks"]
    assert written_fields["proposed_action"] == result["proposed_action"]
    assert written_fields["flagged_reason"] == result["flagged_reason"]


def test_write_back_merges_with_another_agents_existing_checks():
    repo = FakeRepo(
        provider={"id": "p1", "availability": PROVIDER_AVAILABILITY},
        existing_task={"agent_checks": {"insurance_eligibility": {"valid": True}}},
    )

    run_schedule_eligibility_check(
        patient_id="pat1",
        provider_id="p1",
        requested_start=datetime.fromisoformat("2026-06-24T10:00:00+00:00"),
        requested_end=datetime.fromisoformat("2026-06-24T10:30:00+00:00"),
        repo=repo,
        task_id="task-1",
    )

    _, written_fields = repo.updated_tasks[0]
    assert written_fields["agent_checks"]["insurance_eligibility"] == {"valid": True}
    assert "scheduling_eligibility" in written_fields["agent_checks"]


def test_no_task_id_does_not_touch_the_tasks_table():
    repo = FakeRepo(provider={"id": "p1", "availability": PROVIDER_AVAILABILITY})

    run_schedule_eligibility_check(
        patient_id="pat1",
        provider_id="p1",
        requested_start=datetime.fromisoformat("2026-06-24T10:00:00+00:00"),
        requested_end=datetime.fromisoformat("2026-06-24T10:30:00+00:00"),
        repo=repo,
    )

    assert repo.updated_tasks == []


def test_conflicting_slot_is_pending_approval_without_a_proposed_action():
    existing = [
        {
            "id": "other",
            "status": "scheduled",
            "start_time": "2026-06-24T10:00:00+00:00",
            "end_time": "2026-06-24T10:30:00+00:00",
        }
    ]
    repo = FakeRepo(provider={"id": "p1", "availability": PROVIDER_AVAILABILITY}, appointments=existing)

    result = run_schedule_eligibility_check(
        patient_id="pat1",
        provider_id="p1",
        requested_start=datetime.fromisoformat("2026-06-24T10:00:00+00:00"),
        requested_end=datetime.fromisoformat("2026-06-24T10:30:00+00:00"),
        repo=repo,
    )

    assert result["eligible"] is False
    assert result["status"] == "pending_approval"
    assert result["proposed_action"] is None
    assert result["checks"]["scheduling_eligibility"]["conflict"] is True


def test_three_consecutive_reschedules_escalates_for_a_manual_call():
    repo = FakeRepo(
        provider={"id": "p1", "availability": PROVIDER_AVAILABILITY},
        reschedule_tasks=[{"id": "t1"}, {"id": "t2"}],
    )

    result = run_schedule_eligibility_check(
        patient_id="pat1",
        provider_id="p1",
        requested_start=datetime.fromisoformat("2026-06-24T10:00:00+00:00"),
        requested_end=datetime.fromisoformat("2026-06-24T10:30:00+00:00"),
        repo=repo,
    )

    assert result["eligible"] is False
    assert result["status"] == "escalated"
    assert "manual" in result["flagged_reason"] or "call" in result["flagged_reason"]
    assert result["checks"]["scheduling_eligibility"]["consecutive_reschedule_count"] == 2
    assert result["proposed_action"] is None


def test_missing_provider_raises_a_not_found_error():
    repo = FakeRepo(provider=None)

    with pytest.raises(ProviderNotFoundError):
        run_schedule_eligibility_check(
            patient_id="pat1",
            provider_id="missing-provider",
            requested_start=datetime.fromisoformat("2026-06-24T10:00:00+00:00"),
            requested_end=datetime.fromisoformat("2026-06-24T10:30:00+00:00"),
            repo=repo,
        )
