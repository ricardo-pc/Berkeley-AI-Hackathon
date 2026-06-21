from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


RequestType = Literal["refill", "reschedule", "message_relay", "unknown"]
UrgencySignal = Literal["routine", "urgent", "emergency", "unknown"]


class IntakeRequestDetails(BaseModel):
    type: RequestType = "unknown"
    details: str = ""
    orders: List[str] = Field(default_factory=list)
    preferred_times: List[Dict[str, Any]] = Field(default_factory=list)
    urgency_signal: UrgencySignal = "unknown"


class IntakeExtraction(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = Field(
        default=None,
        description="Patient date of birth in YYYY-MM-DD if stated.",
    )
    phone_number: Optional[str] = None
    insurance_plan: Optional[str] = None
    request: IntakeRequestDetails = Field(default_factory=IntakeRequestDetails)
    requests: List[IntakeRequestDetails] = Field(default_factory=list)
    missing_fields: List[str] = Field(default_factory=list)
    transcript: str = ""

    def model_post_init(self, __context: Any) -> None:
        if not self.requests:
            self.requests = [self.request]
        elif _is_default_request(self.request):
            self.request = self.requests[0]


class IntakeExtractionRequest(BaseModel):
    stt_json: Dict[str, Any]


def to_plain_dict(model: BaseModel) -> dict:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _is_default_request(request: IntakeRequestDetails) -> bool:
    return (
        request.type == "unknown"
        and request.details == ""
        and request.orders == []
        and request.preferred_times == []
        and request.urgency_signal == "unknown"
    )
