from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

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


@dataclass(frozen=True)
class TelephonyConfig:
    provider: Literal["twilio", "signalwire"]
    account_sid: str | None
    auth_token: str | None
    signing_key: str | None
    validate_signature: bool
    public_base_url: str | None
    recording_format: str  # "wav" or "mp3"
    greeting: str | None
    max_recording_seconds: int


DEFAULT_MAX_RECORDING_SECONDS = 120
DEFAULT_PROVIDER = "twilio"


def get_telephony_config() -> TelephonyConfig:
    load_environment()
    provider = _provider(os.getenv("TELEPHONY_PROVIDER"))
    recording_format = (
        os.getenv("TELEPHONY_RECORDING_FORMAT")
        or os.getenv(f"{provider.upper()}_RECORDING_FORMAT")
        or os.getenv("TWILIO_RECORDING_FORMAT")
        or "wav"
    ).strip().lower()
    if recording_format not in {"wav", "mp3"}:
        recording_format = "wav"

    account_sid, auth_token, signing_key = _provider_credentials(provider)

    return TelephonyConfig(
        provider=provider,
        account_sid=account_sid,
        auth_token=auth_token,
        signing_key=signing_key,
        validate_signature=_as_bool(
            os.getenv("TELEPHONY_VALIDATE_SIGNATURE")
            or os.getenv(f"{provider.upper()}_VALIDATE_SIGNATURE")
            or os.getenv("TWILIO_VALIDATE_SIGNATURE"),
            default=True,
        ),
        public_base_url=_normalize_base_url(
            os.getenv("TELEPHONY_PUBLIC_BASE_URL") or os.getenv("PUBLIC_BASE_URL")
        ),
        recording_format=recording_format,
        greeting=_strip_or_none(
            os.getenv("TELEPHONY_GREETING")
            or os.getenv(f"{provider.upper()}_GREETING")
            or os.getenv("TWILIO_GREETING")
        ),
        max_recording_seconds=_as_int(
            os.getenv("TELEPHONY_MAX_RECORDING_SECONDS")
            or os.getenv(f"{provider.upper()}_MAX_RECORDING_SECONDS")
            or os.getenv("TWILIO_MAX_RECORDING_SECONDS"),
            default=DEFAULT_MAX_RECORDING_SECONDS,
        ),
    )


def get_twilio_config() -> TelephonyConfig:
    return get_telephony_config()


TwilioConfig = TelephonyConfig


def _provider(value: str | None) -> Literal["twilio", "signalwire"]:
    normalized = (value or DEFAULT_PROVIDER).strip().lower()
    if normalized in {"signalwire", "signal_wire"}:
        return "signalwire"
    return "twilio"


def _provider_credentials(provider: Literal["twilio", "signalwire"]) -> tuple[str | None, str | None, str | None]:
    if provider == "signalwire":
        signing_key = _strip_or_none(
            os.getenv("SIGNALWIRE_SIGNING_KEY") or os.getenv("SIGNALWIRE_AUTH_TOKEN")
        )
        return (
            _strip_or_none(os.getenv("SIGNALWIRE_PROJECT_ID")),
            _strip_or_none(os.getenv("SIGNALWIRE_API_TOKEN")),
            signing_key,
        )

    auth_token = _strip_or_none(os.getenv("TWILIO_AUTH_TOKEN"))
    return (
        _strip_or_none(os.getenv("TWILIO_ACCOUNT_SID")),
        auth_token,
        auth_token,
    )


def _strip_or_none(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _normalize_base_url(value: str | None) -> str | None:
    base = _strip_or_none(value)
    if base is None:
        return None
    return base.rstrip("/")


def _as_bool(value: str | None, *, default: bool) -> bool:
    if value is None or not value.strip():
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_int(value: str | None, *, default: int) -> int:
    if value is None or not value.strip():
        return default
    try:
        return int(value.strip())
    except ValueError:
        return default
