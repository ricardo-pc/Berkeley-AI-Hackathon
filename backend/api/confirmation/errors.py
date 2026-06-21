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


class MissingTextbeltConfigError(ConfirmationError):
    code = "missing_textbelt_config"
    status_code = 500

    def __init__(self):
        super().__init__("TEXTBELT_API_KEY not configured.")


class TextbeltSendError(ConfirmationError):
    code = "textbelt_send_failed"
    status_code = 502

    def __init__(self, detail: str):
        super().__init__(f"Textbelt failed to send the message: {detail}")


def error_payload(exc: ConfirmationError) -> dict:
    return {
        "error": {
            "code": exc.code,
            "message": str(exc),
        }
    }
