from __future__ import annotations


class TelephonyError(Exception):
    code = "telephony_error"
    status_code = 500

    def __init__(self, message: str | None = None):
        super().__init__(message or "Telephony processing failed.")


class MissingTelephonyCredentialsError(TelephonyError):
    code = "missing_telephony_credentials"
    status_code = 500

    def __init__(self, provider: str):
        super().__init__(
            f"{provider.title()} credentials are not configured for recording download."
        )


class MissingTwilioCredentialsError(MissingTelephonyCredentialsError):
    code = "missing_twilio_credentials"

    def __init__(self):
        super().__init__("Twilio")


class RecordingDownloadError(TelephonyError):
    code = "recording_download_failed"
    status_code = 502

    def __init__(self, message: str = "Could not download the voicemail recording."):
        super().__init__(message)


class InvalidTelephonySignatureError(TelephonyError):
    code = "invalid_telephony_signature"
    status_code = 403

    def __init__(self, provider: str):
        super().__init__(f"Request signature did not match the configured {provider.title()} secret.")


class InvalidTwilioSignatureError(InvalidTelephonySignatureError):
    code = "invalid_twilio_signature"

    def __init__(self):
        super().__init__("Twilio")


def error_payload(exc: TelephonyError) -> dict:
    return {
        "error": {
            "code": exc.code,
            "message": str(exc),
        }
    }
