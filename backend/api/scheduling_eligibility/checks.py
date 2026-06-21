from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Iterable

from .constants import (
    ALTERNATIVE_SLOT_SEARCH_DAYS,
    ALTERNATIVE_SLOT_STEP_MINUTES,
    CONSECUTIVE_RESCHEDULE_THRESHOLD,
    HOLIDAYS,
    WEEKDAY_KEYS,
)


def check_calendar_conflict(
    *,
    requested_start: datetime,
    requested_end: datetime,
    provider_availability: dict[str, list[str]],
    existing_appointments: Iterable[dict[str, Any]],
    exclude_appointment_id: str | None = None,
) -> tuple[bool, str | None]:
    """Checks the requested slot against holidays, provider hours, and booked appointments."""
    requested_date = requested_start.date().isoformat()
    if requested_date in HOLIDAYS:
        return True, f"{requested_date} is a clinic holiday."

    hours = provider_availability.get(WEEKDAY_KEYS[requested_start.weekday()])
    if not hours:
        return True, "Provider does not work on the requested day."

    work_start = _combine(requested_start, hours[0])
    work_end = _combine(requested_start, hours[1])
    if requested_start < work_start or requested_end > work_end:
        return True, f"Requested time is outside provider availability ({hours[0]}-{hours[1]})."

    for appointment in existing_appointments:
        if exclude_appointment_id and appointment.get("id") == exclude_appointment_id:
            continue
        if appointment.get("status") != "scheduled":
            continue

        other_start = _as_datetime(appointment["start_time"])
        other_end = _as_datetime(appointment["end_time"])
        if requested_start < other_end and requested_end > other_start:
            return True, "Requested time overlaps an existing appointment."

    return False, None


def find_next_available_slot(
    *,
    requested_start: datetime,
    duration: timedelta,
    provider_availability: dict[str, list[str]],
    existing_appointments: list[dict[str, Any]],
    exclude_appointment_id: str | None = None,
    search_days: int = ALTERNATIVE_SLOT_SEARCH_DAYS,
    step_minutes: int = ALTERNATIVE_SLOT_STEP_MINUTES,
) -> tuple[datetime, datetime] | None:
    """Searches forward from the requested time for the soonest open slot of the same duration.

    Re-checks the same (already-fetched) existing_appointments against every
    candidate via check_calendar_conflict, so holidays/provider-hours/overlaps
    are all honored automatically. Returns None if nothing opens up within
    search_days.
    """
    day_start = requested_start.replace(hour=0, minute=0, second=0, microsecond=0)

    for day_offset in range(search_days):
        day = day_start + timedelta(days=day_offset)
        for minutes in range(0, 24 * 60, step_minutes):
            candidate_start = day + timedelta(minutes=minutes)
            if candidate_start < requested_start:
                continue

            candidate_end = candidate_start + duration
            conflict, _reason = check_calendar_conflict(
                requested_start=candidate_start,
                requested_end=candidate_end,
                provider_availability=provider_availability,
                existing_appointments=existing_appointments,
                exclude_appointment_id=exclude_appointment_id,
            )
            if not conflict:
                return candidate_start, candidate_end

    return None


def check_consecutive_reschedules(
    *,
    reschedule_tasks_since_last_visit: list[dict[str, Any]],
) -> tuple[int, bool]:
    """Returns (prior request count, whether a manual call is required for this new request)."""
    count = len(reschedule_tasks_since_last_visit)
    return count, count >= CONSECUTIVE_RESCHEDULE_THRESHOLD


def _combine(day: datetime, time_str: str) -> datetime:
    hour, minute = (int(part) for part in time_str.split(":"))
    return day.replace(hour=hour, minute=minute, second=0, microsecond=0)


def _as_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
