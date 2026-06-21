from __future__ import annotations

from typing import Any, Callable

from .templates import build_confirmation_message
from .twilio_client import send_sms


def send_confirmation(
    *,
    task_type: str,
    phone_number: str,
    result: dict[str, Any],
    sender: Callable[..., dict[str, Any]] = send_sms,
) -> dict[str, Any] | None:
    """Sends a confirmation text for a successfully executed refill or reschedule.

    Returns None (no text sent) for message_relay or any executor result with
    success: False — there's nothing confirmed to tell the patient about yet.
    """
    if not result.get("success"):
        return None

    message = build_confirmation_message(task_type, result)
    if message is None:
        return None

    return sender(phone_number, message)
