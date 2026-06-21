from __future__ import annotations

import os
from typing import Any

from .errors import MissingTwilioConfigError

try:
    from dotenv import find_dotenv, load_dotenv
except ImportError:  # pragma: no cover - python-dotenv is listed in requirements.
    find_dotenv = None
    load_dotenv = None


def load_environment() -> None:
    if not find_dotenv or not load_dotenv:
        return
    env_path = find_dotenv(usecwd=True)
    if env_path:
        load_dotenv(env_path)


def get_twilio_config(
    account_sid: str | None = None,
    auth_token: str | None = None,
    from_number: str | None = None,
) -> tuple[str, str, str]:
    load_environment()
    resolved_sid = account_sid if account_sid is not None else os.getenv("TWILIO_ACCOUNT_SID")
    resolved_token = auth_token if auth_token is not None else os.getenv("TWILIO_AUTH_TOKEN")
    resolved_from = from_number if from_number is not None else os.getenv("TWILIO_FROM_NUMBER")
    if not resolved_sid or not resolved_token or not resolved_from:
        raise MissingTwilioConfigError()
    return resolved_sid, resolved_token, resolved_from


def send_sms(
    to: str,
    body: str,
    *,
    account_sid: str | None = None,
    auth_token: str | None = None,
    from_number: str | None = None,
    client: Any | None = None,
) -> dict[str, Any]:
    resolved_sid, resolved_token, resolved_from = get_twilio_config(account_sid, auth_token, from_number)

    if client is None:
        from twilio.rest import Client

        client = Client(resolved_sid, resolved_token)

    message = client.messages.create(to=to, from_=resolved_from, body=body)
    return {"sid": message.sid, "status": message.status, "to": to, "body": body}
