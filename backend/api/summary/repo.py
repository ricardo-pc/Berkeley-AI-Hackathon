from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Protocol

from .errors import MissingSupabaseConfigError

try:
    from dotenv import find_dotenv, load_dotenv
except ImportError:  # pragma: no cover - python-dotenv is listed in requirements.
    find_dotenv = None
    load_dotenv = None


class SummaryRepo(Protocol):
    def get_tasks(self, since: datetime | None) -> list[dict[str, Any]]: ...

    def get_patients(self, patient_ids: list[str]) -> dict[str, dict[str, Any]]: ...

    def get_patients_with_invalid_insurance(self) -> list[dict[str, Any]]: ...


def load_environment() -> None:
    if not find_dotenv or not load_dotenv:
        return
    env_path = find_dotenv(usecwd=True)
    if env_path:
        load_dotenv(env_path)


class SupabaseSummaryRepo:
    """Reads tasks/patients from Supabase using the service role key. Read-only."""

    def __init__(self, client: Any | None = None):
        self._client = client or _build_supabase_client()

    def get_tasks(self, since: datetime | None) -> list[dict[str, Any]]:
        query = self._client.table("tasks").select("*")
        if since:
            query = query.gte("created_at", since.isoformat())
        return query.execute().data or []

    def get_patients(self, patient_ids: list[str]) -> dict[str, dict[str, Any]]:
        ids = [patient_id for patient_id in set(patient_ids) if patient_id]
        if not ids:
            return {}
        response = self._client.table("patients").select("*").in_("id", ids).execute()
        return {patient["id"]: patient for patient in response.data or []}

    def get_patients_with_invalid_insurance(self) -> list[dict[str, Any]]:
        response = self._client.table("patients").select("*").eq("insurance_valid", False).execute()
        return response.data or []


def _build_supabase_client() -> Any:
    load_environment()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise MissingSupabaseConfigError()

    from supabase import create_client  # imported lazily so tests don't need the package configured

    return create_client(url, key)
