from __future__ import annotations

from datetime import datetime, timedelta, timezone

from scheduling_eligibility.checks import (
    check_calendar_conflict,
    check_consecutive_reschedules,
    find_next_available_slot,
)

PROVIDER_AVAILABILITY = {
    "mon": ["09:00", "17:00"],
    "tue": ["09:00", "17:00"],
    "wed": ["09:00", "17:00"],
    "thu": ["09:00", "17:00"],
    "fri": ["09:00", "17:00"],
}


def _slot(start_iso: str, end_iso: str) -> tuple[datetime, datetime]:
    return datetime.fromisoformat(start_iso), datetime.fromisoformat(end_iso)


def test_open_slot_has_no_conflict():
    start, end = _slot("2026-06-24T10:00:00+00:00", "2026-06-24T10:30:00+00:00")

    conflict, reason = check_calendar_conflict(
        requested_start=start,
        requested_end=end,
        provider_availability=PROVIDER_AVAILABILITY,
        existing_appointments=[],
    )

    assert conflict is False
    assert reason is None


def test_holiday_is_a_conflict():
    start, end = _slot("2026-07-04T10:00:00+00:00", "2026-07-04T10:30:00+00:00")

    conflict, reason = check_calendar_conflict(
        requested_start=start,
        requested_end=end,
        provider_availability=PROVIDER_AVAILABILITY,
        existing_appointments=[],
    )

    assert conflict is True
    assert "holiday" in reason


def test_outside_provider_hours_is_a_conflict():
    start, end = _slot("2026-06-24T18:00:00+00:00", "2026-06-24T18:30:00+00:00")

    conflict, reason = check_calendar_conflict(
        requested_start=start,
        requested_end=end,
        provider_availability=PROVIDER_AVAILABILITY,
        existing_appointments=[],
    )

    assert conflict is True
    assert "availability" in reason


def test_day_provider_does_not_work_is_a_conflict():
    start, end = _slot("2026-06-27T10:00:00+00:00", "2026-06-27T10:30:00+00:00")  # Saturday

    conflict, reason = check_calendar_conflict(
        requested_start=start,
        requested_end=end,
        provider_availability=PROVIDER_AVAILABILITY,
        existing_appointments=[],
    )

    assert conflict is True
    assert "does not work" in reason


def test_overlapping_booked_appointment_is_a_conflict():
    start, end = _slot("2026-06-24T15:00:00+00:00", "2026-06-24T15:30:00+00:00")
    existing = [
        {
            "id": "other-appt",
            "status": "scheduled",
            "start_time": "2026-06-24T15:15:00+00:00",
            "end_time": "2026-06-24T15:45:00+00:00",
        }
    ]

    conflict, reason = check_calendar_conflict(
        requested_start=start,
        requested_end=end,
        provider_availability=PROVIDER_AVAILABILITY,
        existing_appointments=existing,
    )

    assert conflict is True
    assert "overlaps" in reason


def test_excluding_the_appointment_being_moved_avoids_self_conflict():
    start, end = _slot("2026-06-24T15:00:00+00:00", "2026-06-24T15:30:00+00:00")
    existing = [
        {
            "id": "appt-being-moved",
            "status": "scheduled",
            "start_time": "2026-06-24T15:00:00+00:00",
            "end_time": "2026-06-24T15:30:00+00:00",
        }
    ]

    conflict, reason = check_calendar_conflict(
        requested_start=start,
        requested_end=end,
        provider_availability=PROVIDER_AVAILABILITY,
        existing_appointments=existing,
        exclude_appointment_id="appt-being-moved",
    )

    assert conflict is False
    assert reason is None


def test_cancelled_appointments_do_not_block_a_slot():
    start, end = _slot("2026-06-24T15:00:00+00:00", "2026-06-24T15:30:00+00:00")
    existing = [
        {
            "id": "cancelled-appt",
            "status": "cancelled",
            "start_time": "2026-06-24T15:00:00+00:00",
            "end_time": "2026-06-24T15:30:00+00:00",
        }
    ]

    conflict, reason = check_calendar_conflict(
        requested_start=start,
        requested_end=end,
        provider_availability=PROVIDER_AVAILABILITY,
        existing_appointments=existing,
    )

    assert conflict is False
    assert reason is None


def test_no_prior_reschedules_does_not_require_a_call():
    count, requires_call = check_consecutive_reschedules(reschedule_tasks_since_last_visit=[])

    assert count == 0
    assert requires_call is False


def test_two_prior_consecutive_reschedules_require_a_manual_call():
    count, requires_call = check_consecutive_reschedules(
        reschedule_tasks_since_last_visit=[{"id": "t1"}, {"id": "t2"}],
    )

    assert count == 2
    assert requires_call is True


def test_one_prior_reschedule_does_not_require_a_call():
    count, requires_call = check_consecutive_reschedules(
        reschedule_tasks_since_last_visit=[{"id": "t1"}],
    )

    assert count == 1
    assert requires_call is False


def test_find_next_available_slot_returns_same_day_opening_right_after_conflict():
    start, end = _slot("2026-06-24T10:00:00+00:00", "2026-06-24T10:30:00+00:00")
    existing = [
        {"id": "other", "status": "scheduled", "start_time": "2026-06-24T10:00:00+00:00", "end_time": "2026-06-24T10:30:00+00:00"}
    ]

    found = find_next_available_slot(
        requested_start=start,
        duration=end - start,
        provider_availability=PROVIDER_AVAILABILITY,
        existing_appointments=existing,
    )

    assert found == (
        datetime.fromisoformat("2026-06-24T10:30:00+00:00"),
        datetime.fromisoformat("2026-06-24T11:00:00+00:00"),
    )


def test_find_next_available_slot_skips_a_fully_booked_day():
    start, end = _slot("2026-06-24T09:00:00+00:00", "2026-06-24T09:30:00+00:00")
    # Block every 30-minute slot in the working day so it has to roll to the next day.
    existing = [
        {
            "id": f"appt-{hour}",
            "status": "scheduled",
            "start_time": f"2026-06-24T{hour:02d}:00:00+00:00",
            "end_time": f"2026-06-24T{hour:02d}:30:00+00:00",
        }
        for hour in range(9, 17)
    ] + [
        {
            "id": f"appt-{hour}-30",
            "status": "scheduled",
            "start_time": f"2026-06-24T{hour:02d}:30:00+00:00",
            "end_time": f"2026-06-24T{hour + 1:02d}:00:00+00:00",
        }
        for hour in range(9, 17)
    ]

    found = find_next_available_slot(
        requested_start=start,
        duration=end - start,
        provider_availability=PROVIDER_AVAILABILITY,
        existing_appointments=existing,
    )

    assert found is not None
    found_start, _ = found
    assert found_start.date().isoformat() == "2026-06-25"


def test_find_next_available_slot_excludes_the_appointment_being_moved():
    start, end = _slot("2026-06-24T10:00:00+00:00", "2026-06-24T10:30:00+00:00")
    existing = [
        {"id": "appt-being-moved", "status": "scheduled", "start_time": "2026-06-24T10:00:00+00:00", "end_time": "2026-06-24T10:30:00+00:00"}
    ]

    found = find_next_available_slot(
        requested_start=start,
        duration=end - start,
        provider_availability=PROVIDER_AVAILABILITY,
        existing_appointments=existing,
        exclude_appointment_id="appt-being-moved",
    )

    # The requested slot itself is immediately available once its own appointment is excluded.
    assert found == (start, end)


def test_find_next_available_slot_returns_none_when_provider_never_works():
    start, end = _slot("2026-06-24T10:00:00+00:00", "2026-06-24T10:30:00+00:00")

    found = find_next_available_slot(
        requested_start=start,
        duration=end - start,
        provider_availability={},
        existing_appointments=[],
        search_days=3,
    )

    assert found is None


def test_find_next_available_slot_never_proposes_before_the_requested_time():
    start, end = _slot("2026-06-24T14:00:00+00:00", "2026-06-24T14:30:00+00:00")

    found = find_next_available_slot(
        requested_start=start,
        duration=end - start,
        provider_availability=PROVIDER_AVAILABILITY,
        existing_appointments=[],
    )

    found_start, _ = found
    assert found_start >= start
