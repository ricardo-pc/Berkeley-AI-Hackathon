from __future__ import annotations


class SummaryError(Exception):
    code = "summary_error"
    status_code = 500

    def __init__(self, message: str | None = None):
        super().__init__(message or "Failed to build the daily digest.")


class MissingSupabaseConfigError(SummaryError):
    code = "missing_supabase_config"
    status_code = 500

    def __init__(self):
        super().__init__("Supabase URL/service role key not configured.")


def error_payload(exc: SummaryError) -> dict:
    return {
        "error": {
            "code": exc.code,
            "message": str(exc),
        }
    }
