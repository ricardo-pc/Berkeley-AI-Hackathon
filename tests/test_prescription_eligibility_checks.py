from __future__ import annotations

from datetime import datetime

from prescription_eligibility.checks import (
    check_conflicting_medication,
    check_dosage_match,
    check_recent_visit,
    check_upcoming_visit,
    determine_visit_window_months,
    find_identical_prior_prescription,
)

NOW = datetime.fromisoformat("2026-06-20T00:00:00+00:00")


def test_younger_patient_gets_the_short_window():
    dob = datetime.fromisoformat("1978-03-12T00:00:00+00:00")  # ~48 years old

    assert determine_visit_window_months(dob, now=NOW) == 6


def test_older_patient_gets_the_long_window():
    dob = datetime.fromisoformat("1952-01-30T00:00:00+00:00")  # ~74 years old

    assert determine_visit_window_months(dob, now=NOW) == 12


def test_visit_five_months_ago_is_within_the_six_month_window():
    appointments = [
        {"status": "scheduled", "start_time": "2026-01-10T10:00:00+00:00"},
    ]

    ok, last_visit = check_recent_visit(appointments=appointments, window_months=6, now=NOW)

    assert ok is True
    assert last_visit == "2026-01-10T10:00:00+00:00"


def test_visit_nineteen_months_ago_is_outside_even_the_twelve_month_window():
    appointments = [
        {"status": "scheduled", "start_time": "2024-11-20T09:00:00+00:00"},
    ]

    ok, last_visit = check_recent_visit(appointments=appointments, window_months=12, now=NOW)

    assert ok is False
    assert last_visit == "2024-11-20T09:00:00+00:00"


def test_no_past_visits_fails_the_recent_visit_check():
    ok, last_visit = check_recent_visit(appointments=[], window_months=6, now=NOW)

    assert ok is False
    assert last_visit is None


def test_appointment_within_a_year_counts_as_upcoming():
    appointments = [
        {"status": "scheduled", "start_time": "2026-09-15T10:00:00+00:00"},
    ]

    assert check_upcoming_visit(appointments=appointments, now=NOW) is True


def test_only_past_appointments_means_no_upcoming_visit():
    appointments = [
        {"status": "scheduled", "start_time": "2024-11-20T09:00:00+00:00"},
    ]

    assert check_upcoming_visit(appointments=appointments, now=NOW) is False


def test_identical_prior_prescription_is_a_dosage_match():
    prior = [
        {"medication_name": "Lisinopril", "dosage": "10mg", "instructions": "once daily with food"},
    ]

    ever_prescribed, dosage_match = check_dosage_match(
        medication_name="Lisinopril",
        dosage="10mg",
        instructions="once daily with food",
        prior_prescriptions=prior,
    )

    assert ever_prescribed is True
    assert dosage_match is True


def test_identical_prior_prescription_returns_the_latest_exact_db_row():
    prior = [
        {
            "id": "old-dose",
            "medication_name": "Lisinopril",
            "dosage": "5mg",
            "instructions": "once daily with food",
            "prescribed_at": "2026-02-01T10:00:00+00:00",
        },
        {
            "id": "older-match",
            "medication_name": "Lisinopril",
            "dosage": "10mg",
            "instructions": "once daily with food",
            "prescribed_at": "2026-01-01T10:00:00+00:00",
        },
        {
            "id": "latest-match",
            "medication_name": "Lisinopril",
            "dosage": "10mg",
            "instructions": "once daily with food",
            "prescribed_at": "2026-03-01T10:00:00+00:00",
        },
    ]

    match = find_identical_prior_prescription(
        medication_name="Lisinopril",
        dosage="10mg",
        instructions="once daily with food",
        prior_prescriptions=prior,
    )

    assert match["id"] == "latest-match"


def test_different_dosage_is_not_a_match_even_if_prescribed_before():
    prior = [
        {"medication_name": "Lisinopril", "dosage": "5mg", "instructions": "once daily with food"},
    ]

    ever_prescribed, dosage_match = check_dosage_match(
        medication_name="Lisinopril",
        dosage="10mg",
        instructions="once daily with food",
        prior_prescriptions=prior,
    )

    assert ever_prescribed is True
    assert dosage_match is False


def test_never_prescribed_before_fails_outright():
    ever_prescribed, dosage_match = check_dosage_match(
        medication_name="Metformin",
        dosage="500mg",
        instructions="twice daily",
        prior_prescriptions=[],
    )

    assert ever_prescribed is False
    assert dosage_match is False


def test_known_conflicting_medication_is_flagged():
    active = [{"medication_name": "Amlodipine"}]

    conflict, conflict_medication = check_conflicting_medication(
        medication_name="Lisinopril", active_prescriptions=active
    )

    assert conflict is True
    assert conflict_medication == "Amlodipine"


def test_unrelated_active_medication_is_not_a_conflict():
    active = [{"medication_name": "Sertraline"}]

    conflict, conflict_medication = check_conflicting_medication(
        medication_name="Lisinopril", active_prescriptions=active
    )

    assert conflict is False
    assert conflict_medication is None
