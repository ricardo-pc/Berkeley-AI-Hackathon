from __future__ import annotations

import logging
from typing import Mapping

from twilio.request_validator import RequestValidator

from .config import TelephonyConfig

logger = logging.getLogger("telephony")


def request_is_authentic(
    *,
    url: str,
    params: Mapping[str, str],
    signature: str,
    config: TelephonyConfig,
) -> bool:
    """Validate the configured provider's webhook signature against the request.

    Validation is skipped when explicitly disabled (handy for local testing) or
    when no provider signing secret is configured; both cases are logged so
    they are not silent in production.
    """
    if not config.validate_signature:
        return True

    if config.provider == "signalwire":
        if not config.signing_key:
            logger.warning(
                "SIGNALWIRE_SIGNING_KEY is not set; skipping SignalWire signature validation."
            )
            return True
        return _signalwire_request_is_authentic(
            url=url,
            params=params,
            signature=signature,
            signing_key=config.signing_key,
        )

    if not config.signing_key:
        logger.warning(
            "TWILIO_AUTH_TOKEN is not set; skipping Twilio signature validation."
        )
        return True

    validator = RequestValidator(config.signing_key)
    return validator.validate(url, dict(params), signature or "")


def _signalwire_request_is_authentic(
    *,
    url: str,
    params: Mapping[str, str],
    signature: str,
    signing_key: str,
) -> bool:
    # SignalWire Compatibility callbacks use the same signed URL + form-param
    # validation shape as Twilio, but the header name and secret differ.
    validator = RequestValidator(signing_key)
    return validator.validate(url, dict(params), signature or "")


def public_base_url(config: TelephonyConfig, *, fallback: str) -> str:
    """Absolute base URL used to build callback URLs the provider can reach."""
    if config.public_base_url:
        return config.public_base_url
    return fallback.rstrip("/")
