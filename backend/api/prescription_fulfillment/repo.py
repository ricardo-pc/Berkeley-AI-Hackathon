from __future__ import annotations

import os
from typing import Any, Protocol

from .errors import MissingSupabaseConfigError, RefillFailedError

try:
    from dotenv import find_dotenv, load_dotenv
except ImportError:  # pragma: no cover - python-dotenv is listed in requirements.
    find_dotenv = None
    load_dotenv = None


class PrescriptionFulfillmentRepo(Protocol):
    def get_patient(self, patient_id: str) -> dict[str, Any] | None: ...

    def insert_prescription(
        self,
        *,
        patient_id: str,
        provider_id: str,
        medication_name: str,
        dosage: str,
        instructions: str,
    ) -> dict[str, Any]: ...

    def update_task(self, task_id: str, fields: dict[str, Any]) -> None: ...


def load_environment() -> None:
    if not find_dotenv or not load_dotenv:
        return
    env_path = find_dotenv(usecwd=True)
    if env_path:
        load_dotenv(env_path)


class SupabasePrescriptionFulfillmentRepo:
    """Resolves the patient and writes the refill to Supabase using the service role key."""

    def __init__(self, client: Any | None = None):
        self._client = client or _build_supabase_client()

    def get_patient(self, patient_id: str) -> dict[str, Any] | None:
        response = self._client.table("patients").select("*").eq("id", patient_id).limit(1).execute()
        rows = response.data or []
        return rows[0] if rows else None

    def insert_prescription(
        self,
        *,
        patient_id: str,
        provider_id: str,
        medication_name: str,
        dosage: str,
        instructions: str,
    ) -> dict[str, Any]:
        response = (
            self._client.table("prescriptions")
            .insert(
                {
                    "patient_id": patient_id,
                    "provider_id": provider_id,
                    "medication_name": medication_name,
                    "dosage": dosage,
                    "instructions": instructions,
                    "active": True,
                }
            )
            .execute()
        )
        rows = response.data or []
        if not rows:
            raise RefillFailedError("insert returned no rows")
        return rows[0]

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
