from __future__ import annotations


class ScheduleEligibilityError(Exception):
    code = "schedule_eligibility_error"
    status_code = 500

    def __init__(self, message: str | None = None):
        super().__init__(message or "Schedule eligibility check failed.")


class MissingSupabaseConfigError(ScheduleEligibilityError):
    code = "missing_supabase_config"
    status_code = 500

    def __init__(self):
        super().__init__("Supabase URL/service role key not configured.")


class ProviderNotFoundError(ScheduleEligibilityError):
    code = "provider_not_found"
    status_code = 404

    def __init__(self, provider_id: str):
        super().__init__(f"Provider {provider_id} not found.")


def error_payload(exc: ScheduleEligibilityError) -> dict:
    return {
        "error": {
            "code": exc.code,
            "message": str(exc),
        }
    }
