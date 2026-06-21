from __future__ import annotations


class PrescriptionEligibilityError(Exception):
    code = "prescription_eligibility_error"
    status_code = 500

    def __init__(self, message: str | None = None):
        super().__init__(message or "Prescription eligibility check failed.")


class MissingSupabaseConfigError(PrescriptionEligibilityError):
    code = "missing_supabase_config"
    status_code = 500

    def __init__(self):
        super().__init__("Supabase URL/service role key not configured.")


class MissingAnthropicAPIKeyError(PrescriptionEligibilityError):
    code = "missing_anthropic_api_key"
    status_code = 500

    def __init__(self):
        super().__init__("Anthropic API key not configured.")


class PatientNotFoundError(PrescriptionEligibilityError):
    code = "patient_not_found"
    status_code = 404

    def __init__(self, patient_id: str):
        super().__init__(f"Patient {patient_id} not found.")


def error_payload(exc: PrescriptionEligibilityError) -> dict:
    return {
        "error": {
            "code": exc.code,
            "message": str(exc),
        }
    }
