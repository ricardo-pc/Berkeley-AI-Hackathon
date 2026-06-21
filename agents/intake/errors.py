from __future__ import annotations


class IntakeAgentError(Exception):
    code = "intake_agent_error"
    status_code = 500

    def __init__(self, message: str | None = None):
        super().__init__(message or "Intake extraction failed.")


class MissingAnthropicAPIKeyError(IntakeAgentError):
    code = "missing_anthropic_api_key"
    status_code = 500

    def __init__(self):
        super().__init__("Anthropic API key not configured.")


class InvalidSTTPayloadError(IntakeAgentError):
    code = "invalid_stt_payload"
    status_code = 400

    def __init__(self):
        super().__init__("STT JSON must include a transcript.")


class ClaudeExtractionError(IntakeAgentError):
    code = "claude_extraction_error"
    status_code = 502

    def __init__(self, message: str = "Claude did not return valid intake extraction JSON."):
        super().__init__(message)


def error_payload(exc: IntakeAgentError) -> dict:
    return {
        "error": {
            "code": exc.code,
            "message": str(exc),
        }
    }

