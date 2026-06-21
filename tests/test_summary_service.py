from __future__ import annotations

from datetime import datetime
from typing import Any

from summary.service import build_daily_digest


class FakeRepo:
    def __init__(
        self,
        tasks: list[dict[str, Any]] | None = None,
        patients: dict[str, dict[str, Any]] | None = None,
        invalid_insurance_patients: list[dict[str, Any]] | None = None,
    ):
        self._tasks = tasks or []
        self._patients = patients or {}
        self._invalid_insurance_patients = invalid_insurance_patients or []
        self.requested_since: datetime | None = "not called"

    def get_tasks(self, since: datetime | None) -> list[dict[str, Any]]:
        self.requested_since = since
        return self._tasks

    def get_patients(self, patient_ids: list[str]) -> dict[str, dict[str, Any]]:
        return {pid: self._patients[pid] for pid in patient_ids if pid in self._patients}

    def get_patients_with_invalid_insurance(self) -> list[dict[str, Any]]:
        return self._invalid_insurance_patients


PATIENTS = {
    "pat1": {"id": "pat1", "first_name": "Maria", "last_name": "Gonzalez"},
    "pat2": {"id": "pat2", "first_name": "James", "last_name": "Okafor"},
    "pat3": {"id": "pat3", "first_name": "Robert", "last_name": "Martinez"},
}


def test_buckets_tasks_by_status():
    tasks = [
        {"patient_id": "pat1", "task_type": "prescription_refill", "status": "complete", "agent_summary": "done"},
        {"patient_id": "pat2", "task_type": "prescription_refill", "status": "escalated", "flagged_reason": "too old"},
        {"patient_id": "pat3", "task_type": "reschedule", "status": "pending_approval", "agent_summary": "needs review"},
    ]
    repo = FakeRepo(tasks=tasks, patients=PATIENTS)

    digest = build_daily_digest(since=None, repo=repo)

    assert len(digest["completed"]) == 1
    assert digest["completed"][0]["patient_name"] == "Maria Gonzalez"
    assert len(digest["flagged"]) == 1
    assert digest["flagged"][0]["flagged_reason"] == "too old"
    assert len(digest["pending"]) == 1
    assert digest["pending"][0]["patient_name"] == "Robert Martinez"
    assert digest["counts"] == {
        "completed": 1,
        "flagged": 1,
        "pending": 1,
        "missing_insurance": 0,
        "total_tasks": 3,
    }


def test_unrecognized_status_is_not_counted_in_any_bucket():
    tasks = [{"patient_id": "pat1", "task_type": "reschedule", "status": "rejected"}]
    repo = FakeRepo(tasks=tasks, patients=PATIENTS)

    digest = build_daily_digest(since=None, repo=repo)

    assert digest["completed"] == []
    assert digest["flagged"] == []
    assert digest["pending"] == []
    assert digest["counts"]["total_tasks"] == 1


def test_missing_insurance_comes_from_patients_table_not_agent_checks():
    repo = FakeRepo(
        tasks=[],
        invalid_insurance_patients=[
            {"first_name": "Linda", "last_name": "Chen", "insurance_plan": "Kaiser Permanente"}
        ],
    )

    digest = build_daily_digest(since=None, repo=repo)

    assert digest["missing_insurance"] == [
        {"patient_name": "Linda Chen", "insurance_plan": "Kaiser Permanente"}
    ]
    assert digest["counts"]["missing_insurance"] == 1


def test_unknown_patient_id_falls_back_to_placeholder_name():
    tasks = [{"patient_id": "ghost", "task_type": "reschedule", "status": "pending_approval"}]
    repo = FakeRepo(tasks=tasks, patients=PATIENTS)

    digest = build_daily_digest(since=None, repo=repo)

    assert digest["pending"][0]["patient_name"] == "Unknown patient"


def test_since_filter_is_passed_through_to_the_repo():
    repo = FakeRepo(tasks=[])
    since = datetime.fromisoformat("2026-06-20T00:00:00+00:00")

    build_daily_digest(since=since, repo=repo)

    assert repo.requested_since == since


def test_narrative_is_omitted_when_no_summarizer_given():
    repo = FakeRepo(tasks=[])

    digest = build_daily_digest(since=None, repo=repo)

    assert "narrative" not in digest


def test_narrative_is_included_when_summarizer_given():
    repo = FakeRepo(tasks=[])

    digest = build_daily_digest(since=None, repo=repo, summarize=lambda d: "fake narrative")

    assert digest["narrative"] == "fake narrative"
