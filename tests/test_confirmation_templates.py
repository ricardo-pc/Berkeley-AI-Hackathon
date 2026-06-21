from __future__ import annotations

from confirmation.templates import build_confirmation_message


def test_prescription_refill_message_includes_medication_and_instructions():
    result = {
        "patient": {"first_name": "Maria"},
        "prescription": {"medication_name": "Lisinopril", "dosage": "10mg", "instructions": "once daily with food"},
    }

    message = build_confirmation_message("prescription_refill", result)

    assert message is not None
    assert "Maria" in message
    assert "Lisinopril" in message
    assert "10mg" in message
    assert "once daily with food" in message


def test_reschedule_message_includes_formatted_time():
    result = {
        "patient": {"first_name": "Robert"},
        "appointment": {"start_time": "2026-06-25T09:00:00+00:00"},
    }

    message = build_confirmation_message("reschedule", result)

    assert message is not None
    assert "Robert" in message
    assert "June 25" in message


def test_message_relay_never_gets_a_text():
    result = {"patient": {"first_name": "Priya"}, "worth_relaying": True}

    assert build_confirmation_message("message_relay", result) is None


def test_unknown_task_type_never_gets_a_text():
    assert build_confirmation_message("escalate", {}) is None
