from __future__ import annotations


class MessageRelayError(Exception):
    code = "message_relay_error"
    status_code = 500

    def __init__(self, message: str | None = None):
        super().__init__(message or "Message relay check failed.")


class MissingSupabaseConfigError(MessageRelayError):
    code = "missing_supabase_config"
    status_code = 500

    def __init__(self):
        super().__init__("Supabase URL/service role key not configured.")


class MissingAnthropicAPIKeyError(MessageRelayError):
    code = "missing_anthropic_api_key"
    status_code = 500

    def __init__(self):
        super().__init__("Anthropic API key not configured.")


class PatientNotFoundError(MessageRelayError):
    code = "patient_not_found"
    status_code = 404

    def __init__(self, patient_id: str):
        super().__init__(f"Patient {patient_id} not found.")


def error_payload(exc: MessageRelayError) -> dict:
    return {
        "error": {
            "code": exc.code,
            "message": str(exc),
        }
    }
