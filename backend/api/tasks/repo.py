from __future__ import annotations

import os
from typing import Any

try:
    from dotenv import find_dotenv, load_dotenv
except ImportError:  # pragma: no cover
    find_dotenv = None
    load_dotenv = None


def _load_env() -> None:
    if find_dotenv and load_dotenv:
        path = find_dotenv(usecwd=True)
        if path:
            load_dotenv(path)


def build_client() -> Any:
    _load_env()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError("Missing SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY")
    from supabase import create_client

    return create_client(url, key)


class TasksRepo:
    """Single Supabase entry point for the CHW dashboard's reads/writes:
    tasks + the patient/voicemail joins, plus the relay `messages` insert."""

    def __init__(self, client: Any | None = None):
        self._c = client or build_client()

    # --- tasks ---
    def list_tasks(self) -> list[dict[str, Any]]:
        return self._c.table("tasks").select("*").order("created_at", desc=True).execute().data or []

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        rows = self._c.table("tasks").select("*").eq("id", task_id).limit(1).execute().data or []
        return rows[0] if rows else None

    def update_task(self, task_id: str, fields: dict[str, Any]) -> None:
        self._c.table("tasks").update(fields).eq("id", task_id).execute()

    # --- joins ---
    def patients_by_ids(self, ids: list[str]) -> dict[str, dict[str, Any]]:
        if not ids:
            return {}
        rows = (
            self._c.table("patients")
            .select("id, first_name, last_name, date_of_birth, phone")
            .in_("id", ids)
            .execute()
            .data
            or []
        )
        return {r["id"]: r for r in rows}

    def voicemails_by_ids(self, ids: list[str]) -> dict[str, dict[str, Any]]:
        if not ids:
            return {}
        rows = (
            self._c.table("voicemails").select("id, transcript, audio_url").in_("id", ids).execute().data or []
        )
        return {r["id"]: r for r in rows}

    def get_patient(self, patient_id: str) -> dict[str, Any] | None:
        rows = self._c.table("patients").select("*").eq("id", patient_id).limit(1).execute().data or []
        return rows[0] if rows else None

    # --- relay delivery (message_relay executor) ---
    def insert_message(
        self, *, task_id: str, patient_id: str | None, provider_id: str | None, message_body: str, delivered: bool
    ) -> Any:
        return (
            self._c.table("messages")
            .insert(
                {
                    "task_id": task_id,
                    "patient_id": patient_id,
                    "provider_id": provider_id,
                    "message_body": message_body,
                    "delivered": delivered,
                }
            )
            .execute()
            .data
        )

    # --- demo reset helpers ---
    def list_ids(self, table: str) -> list[str]:
        rows = self._c.table(table).select("id").execute().data or []
        return [r["id"] for r in rows]

    def delete_ids(self, table: str, ids: list[str]) -> None:
        if ids:
            self._c.table(table).delete().in_("id", ids).execute()
