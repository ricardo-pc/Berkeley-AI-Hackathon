from __future__ import annotations

import os
from typing import Any

import httpx

from .errors import MissingTextbeltConfigError, TextbeltSendError

try:
    from dotenv import find_dotenv, load_dotenv
except ImportError:  # pragma: no cover - python-dotenv is listed in requirements.
    find_dotenv = None
    load_dotenv = None


TEXTBELT_URL = "https://textbelt.com/text"


def load_environment() -> None:
    if not find_dotenv or not load_dotenv:
        return
    env_path = find_dotenv(usecwd=True)
    if env_path:
        load_dotenv(env_path)


def get_textbelt_api_key(api_key: str | None = None) -> str:
    load_environment()
    resolved = api_key if api_key is not None else os.getenv("TEXTBELT_API_KEY")
    if not resolved:
        raise MissingTextbeltConfigError()
    return resolved


def send_sms(
    to: str,
    body: str,
    *,
    api_key: str | None = None,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    resolved_key = get_textbelt_api_key(api_key)
    payload = {"phone": to, "message": body, "key": resolved_key}

    if client is not None:
        response = client.post(TEXTBELT_URL, data=payload)
    else:
        response = httpx.post(TEXTBELT_URL, data=payload, timeout=15.0)

    data = response.json()
    if not data.get("success"):
        raise TextbeltSendError(data.get("error") or "unknown error")

    return {
        "sid": data.get("textId"),
        "status": "queued",
        "to": to,
        "body": body,
        "quota_remaining": data.get("quotaRemaining"),
    }
