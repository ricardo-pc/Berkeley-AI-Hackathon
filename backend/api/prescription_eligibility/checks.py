from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from .constants import (
    CONFLICTING_MEDICATIONS,
    LONG_VISIT_WINDOW_MONTHS,
    LONGER_WINDOW_AGE_THRESHOLD,
    SHORT_VISIT_WINDOW_MONTHS,
    UPCOMING_VISIT_WINDOW_DAYS,
)


def determine_visit_window_months(date_of_birth: datetime, *, now: datetime | None = None) -> int:
    """Older patients get the longer recent-visit window (per-doctor policy in real life)."""
    now = now or datetime.now(timezone.utc)
    age_years = (now.date() - date_of_birth.date()).days // 365
    return LONG_VISIT_WINDOW_MONTHS if age_years >= LONGER_WINDOW_AGE_THRESHOLD else SHORT_VISIT_WINDOW_MONTHS


def check_recent_visit(
    *,
    appointments: list[dict[str, Any]],
    window_months: int,
    now: datetime | None = None,
) -> tuple[bool, str | None]:
    """Returns (has a completed visit within the window, that visit's start_time if any)."""
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=window_months * 30)

    past_visits = [
        appointment
        for appointment in appointments
        if appointment.get("status") == "scheduled" and _as_datetime(appointment["start_time"]) <= now
    ]
    if not past_visits:
        return False, None

    most_recent = max(past_visits, key=lambda appointment: _as_datetime(appointment["start_time"]))
    most_recent_start = _as_datetime(most_recent["start_time"])
    return most_recent_start >= cutoff, most_recent["start_time"]


def check_upcoming_visit(
    *,
    appointments: list[dict[str, Any]],
    now: datetime | None = None,
    window_days: int = UPCOMING_VISIT_WINDOW_DAYS,
) -> bool:
    now = now or datetime.now(timezone.utc)
    deadline = now + timedelta(days=window_days)

    return any(
        appointment.get("status") == "scheduled" and now < _as_datetime(appointment["start_time"]) <= deadline
        for appointment in appointments
    )


def check_dosage_match(
    *,
    medication_name: str,
    dosage: str,
    instructions: str,
    prior_prescriptions: list[dict[str, Any]],
) -> tuple[bool, bool]:
    """Returns (ever prescribed this medication before, dosage+instructions identical to that prior prescription)."""
    matches = [
        prescription
        for prescription in prior_prescriptions
        if prescription.get("medication_name", "").strip().lower() == medication_name.strip().lower()
    ]
    if not matches:
        return False, False

    identical = any(
        prescription.get("dosage", "").strip().lower() == dosage.strip().lower()
        and prescription.get("instructions", "").strip().lower() == instructions.strip().lower()
        for prescription in matches
    )
    return True, identical


def check_conflicting_medication(
    *,
    medication_name: str,
    active_prescriptions: list[dict[str, Any]],
) -> tuple[bool, str | None]:
    conflicts_with = CONFLICTING_MEDICATIONS.get(medication_name.strip().lower(), set())
    for prescription in active_prescriptions:
        other_medication = prescription.get("medication_name", "").strip().lower()
        if other_medication in conflicts_with:
            return True, prescription["medication_name"]
    return False, None


def _as_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
