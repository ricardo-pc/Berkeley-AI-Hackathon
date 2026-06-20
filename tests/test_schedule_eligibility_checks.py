from __future__ import annotations

from datetime import datetime, timezone

from scheduling_eligibility.checks import check_calendar_conflict, check_consecutive_reschedules

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
