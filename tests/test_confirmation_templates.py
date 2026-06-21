from __future__ import annotations

from confirmation.templates import build_confirmation_message, build_denial_message


def test_prescription_refill_message_includes_dosage_medication_and_pharmacy():
    result = {
        "patient": {"first_name": "Maria"},
        "prescription": {"medication_name": "Lisinopril", "dosage": "10mg", "instructions": "once daily with food"},
    }

    message = build_confirmation_message("prescription_refill", result)

    assert message is not None
    assert "Maria" in message
    assert "10mg" in message
    assert "Lisinopril" in message
    assert "CVS Pharmacy" in message


def test_reschedule_message_includes_formatted_time_and_doctor_name():
    result = {
        "patient": {"first_name": "Robert"},
        "appointment": {"start_time": "2026-06-25T09:00:00+00:00", "provider_name": "Dr. Sarah Lee"},
    }

    message = build_confirmation_message("reschedule", result)

    assert message is not None
    assert "Robert" in message
    assert "June 25" in message
    assert "Dr. Sarah Lee" in message


def test_reschedule_message_omits_doctor_clause_when_name_missing():
    result = {
        "patient": {"first_name": "Robert"},
        "appointment": {"start_time": "2026-06-25T09:00:00+00:00"},
    }

    message = build_confirmation_message("reschedule", result)

    assert message is not None
    assert "Robert" in message
    assert " with " not in message


def test_message_relay_never_gets_a_text():
    result = {"patient": {"first_name": "Priya"}, "worth_relaying": True}

    assert build_confirmation_message("message_relay", result) is None


def test_unknown_task_type_never_gets_a_text():
    assert build_confirmation_message("escalate", {}) is None


def test_refill_denial_message_asks_patient_to_call_back():
    message = build_denial_message("prescription_refill", "James")

    assert message is not None
    assert "James" in message
    assert "call" in message.lower()
    assert "refill" in message.lower()


def test_reschedule_denial_message_asks_patient_to_call_back():
    message = build_denial_message("reschedule", "Linda")

    assert message is not None
    assert "Linda" in message
    assert "call" in message.lower()


def test_denial_message_does_not_leak_specific_clinical_reasons():
    """Deliberately generic -- the SMS shouldn't repeat drug names, visit history, etc."""
    message = build_denial_message("prescription_refill", "James")

    assert "Amlodipine" not in (message or "")
    assert "visit" not in (message or "").lower()


def test_denial_message_falls_back_to_generic_greeting_without_a_name():
    message = build_denial_message("reschedule", None)

    assert message is not None
    assert "there" in message.lower()


def test_message_relay_never_gets_a_denial_text():
    assert build_denial_message("message_relay", "Priya") is None


def test_unknown_task_type_never_gets_a_denial_text():
    assert build_denial_message("escalate", "Someone") is None
