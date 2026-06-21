from __future__ import annotations


class ConfirmationError(Exception):
    code = "confirmation_error"
    status_code = 500

    def __init__(self, message: str | None = None):
        super().__init__(message or "Confirmation send failed.")


class MissingTwilioConfigError(ConfirmationError):
    code = "missing_twilio_config"
    status_code = 500

    def __init__(self):
        super().__init__("TWILIO_ACCOUNT_SID/TWILIO_AUTH_TOKEN/TWILIO_FROM_NUMBER not configured.")


def error_payload(exc: ConfirmationError) -> dict:
    return {
        "error": {
            "code": exc.code,
            "message": str(exc),
        }
    }
