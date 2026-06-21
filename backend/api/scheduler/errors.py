from __future__ import annotations


class SchedulerError(Exception):
    code = "scheduler_error"
    status_code = 500

    def __init__(self, message: str | None = None):
        super().__init__(message or "Scheduling failed.")


class MissingSupabaseConfigError(SchedulerError):
    code = "missing_supabase_config"
    status_code = 500

    def __init__(self):
        super().__init__("Supabase URL/service role key not configured.")


class BookingFailedError(SchedulerError):
    code = "booking_failed"
    status_code = 502

    def __init__(self, detail: str):
        super().__init__(f"Database did not return the booked appointment: {detail}")


def error_payload(exc: SchedulerError) -> dict:
    return {
        "error": {
            "code": exc.code,
            "message": str(exc),
        }
    }
