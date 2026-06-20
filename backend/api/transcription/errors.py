from __future__ import annotations


class TranscriptionError(Exception):
    code = "transcription_error"
    status_code = 500

    def __init__(self, message: str | None = None):
        super().__init__(message or "Transcription failed.")


class MissingAPIKeyError(TranscriptionError):
    code = "missing_api_key"
    status_code = 500

    def __init__(self):
        super().__init__("Deepgram API key not configured.")


class InvalidAudioError(TranscriptionError):
    code = "invalid_audio"
    status_code = 400

    def __init__(self, message: str = "A non-empty audio file is required in form field 'file'."):
        super().__init__(message)


class ProviderTranscriptionError(TranscriptionError):
    code = "provider_error"
    status_code = 502

    def __init__(self, message: str = "Speech-to-text provider failed.", provider_status_code: int | None = None):
        super().__init__(message)
        self.provider_status_code = provider_status_code


def error_payload(exc: TranscriptionError) -> dict:
    return {
        "error": {
            "code": exc.code,
            "message": str(exc),
        }
    }

