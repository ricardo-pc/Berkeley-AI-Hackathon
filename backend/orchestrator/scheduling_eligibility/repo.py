from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Protocol

from .errors import MissingSupabaseConfigError

try:
    from dotenv import find_dotenv, load_dotenv
except ImportError:  # pragma: no cover - python-dotenv is listed in requirements.
    find_dotenv = None
    load_dotenv = None


class ScheduleEligibilityRepo(Protocol):
    def get_patient(self, patient_id: str) -> dict[str, Any]: ...

    def get_provider(self, provider_id: str) -> dict[str, Any]: ...

    def get_scheduled_appointments(self, provider_id: str) -> list[dict[str, Any]]: ...

    def get_reschedule_tasks_since_last_visit(self, patient_id: str) -> list[dict[str, Any]]: ...

    def get_task(self, task_id: str) -> dict[str, Any]: ...

    def update_task(self, task_id: str, fields: dict[str, Any]) -> None: ...


def load_environment() -> None:
    if not find_dotenv or not load_dotenv:
        return
    env_path = find_dotenv(usecwd=True)
    if env_path:
        load_dotenv(env_path)


class SupabaseScheduleEligibilityRepo:
    """Reads provider/appointment/task data from Supabase using the service role key."""

    def __init__(self, client: Any | None = None):
        self._client = client or _build_supabase_client()

    def get_patient(self, patient_id: str) -> dict[str, Any]:
        response = self._client.table("patients").select("*").eq("id", patient_id).limit(1).execute()
        rows = response.data or []
        return rows[0] if rows else {}

    def get_provider(self, provider_id: str) -> dict[str, Any]:
        response = self._client.table("providers").select("*").eq("id", provider_id).limit(1).execute()
        rows = response.data or []
        return rows[0] if rows else {}

    def get_scheduled_appointments(self, provider_id: str) -> list[dict[str, Any]]:
        response = (
            self._client.table("appointments")
            .select("*")
            .eq("provider_id", provider_id)
            .eq("status", "scheduled")
            .execute()
        )
        return response.data or []

    def get_reschedule_tasks_since_last_visit(self, patient_id: str) -> list[dict[str, Any]]:
        now = datetime.now(timezone.utc).isoformat()
        last_visit = (
            self._client.table("appointments")
            .select("start_time")
            .eq("patient_id", patient_id)
            .lt("start_time", now)
            .order("start_time", desc=True)
            .limit(1)
            .execute()
        )
        since = last_visit.data[0]["start_time"] if last_visit.data else None

        query = (
            self._client.table("tasks")
            .select("*")
            .eq("patient_id", patient_id)
            .eq("task_type", "reschedule")
        )
        if since:
            query = query.gt("created_at", since)

        response = query.execute()
        return response.data or []

    def get_task(self, task_id: str) -> dict[str, Any]:
        response = self._client.table("tasks").select("*").eq("id", task_id).limit(1).execute()
        rows = response.data or []
        return rows[0] if rows else {}

    def update_task(self, task_id: str, fields: dict[str, Any]) -> None:
        self._client.table("tasks").update(fields).eq("id", task_id).execute()


def _build_supabase_client() -> Any:
    load_environment()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise MissingSupabaseConfigError()

    from supabase import create_client  # imported lazily so tests don't need the package configured

    return create_client(url, key)
