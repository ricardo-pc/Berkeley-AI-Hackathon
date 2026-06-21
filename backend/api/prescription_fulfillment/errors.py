from __future__ import annotations


class PrescriptionFulfillmentError(Exception):
    code = "prescription_fulfillment_error"
    status_code = 500

    def __init__(self, message: str | None = None):
        super().__init__(message or "Prescription refill failed.")


class MissingSupabaseConfigError(PrescriptionFulfillmentError):
    code = "missing_supabase_config"
    status_code = 500

    def __init__(self):
        super().__init__("Supabase URL/service role key not configured.")


class RefillFailedError(PrescriptionFulfillmentError):
    code = "refill_failed"
    status_code = 502

    def __init__(self, detail: str):
        super().__init__(f"Database did not return the inserted prescription: {detail}")


def error_payload(exc: PrescriptionFulfillmentError) -> dict:
    return {
        "error": {
            "code": exc.code,
            "message": str(exc),
        }
    }
