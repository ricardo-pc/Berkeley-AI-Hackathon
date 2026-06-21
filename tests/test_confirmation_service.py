from __future__ import annotations

from typing import Any

from confirmation.service import send_confirmation, send_denial_notice


def fake_sender(to: str, body: str) -> dict[str, Any]:
    return {"sid": "SM123", "status": "queued", "to": to, "body": body}


def test_sends_a_text_for_a_successful_refill():
    result = {
        "success": True,
        "patient": {"first_name": "Maria"},
        "prescription": {"medication_name": "Lisinopril", "dosage": "10mg", "instructions": "once daily with food"},
    }

    sent = send_confirmation(
        task_type="prescription_refill", phone_number="+14155550101", result=result, sender=fake_sender
    )

    assert sent is not None
    assert sent["to"] == "+14155550101"
    assert "Lisinopril" in sent["body"]


def test_sends_a_text_for_a_successful_reschedule():
    result = {
        "success": True,
        "patient": {"first_name": "Robert"},
        "appointment": {"start_time": "2026-06-25T09:00:00+00:00"},
    }

    sent = send_confirmation(
        task_type="reschedule", phone_number="+14155550174", result=result, sender=fake_sender
    )

    assert sent is not None
    assert "rescheduled" in sent["body"]


def test_never_sends_a_text_for_message_relay():
    result = {"success": True, "patient": {"first_name": "Priya"}}

    sent = send_confirmation(
        task_type="message_relay", phone_number="+14155550165", result=result, sender=fake_sender
    )

    assert sent is None


def test_never_sends_a_text_when_the_executor_failed():
    result = {"success": False, "error": "patient_not_found"}

    sent = send_confirmation(
        task_type="prescription_refill", phone_number="+14155550101", result=result, sender=fake_sender
    )

    assert sent is None


def test_sends_a_denial_notice_for_an_escalated_refill():
    sent = send_denial_notice(
        task_type="prescription_refill", phone_number="+14155550182", first_name="James", sender=fake_sender
    )

    assert sent is not None
    assert sent["to"] == "+14155550182"
    assert "call" in sent["body"].lower()


def test_sends_a_denial_notice_for_an_escalated_reschedule():
    sent = send_denial_notice(
        task_type="reschedule", phone_number="+14155550193", first_name="Linda", sender=fake_sender
    )

    assert sent is not None
    assert "Linda" in sent["body"]


def test_never_sends_a_denial_notice_for_message_relay():
    sent = send_denial_notice(
        task_type="message_relay", phone_number="+14155550165", first_name="Priya", sender=fake_sender
    )

    assert sent is None
