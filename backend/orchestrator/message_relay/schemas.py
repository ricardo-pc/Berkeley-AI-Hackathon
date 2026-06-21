from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel


class MessageRelayRequest(BaseModel):
    """Input to the message relay eligibility agent.

    patient_id is the canonical lookup key (uniform with the other eligibility
    agents); first/last/dob are always carried for output and human review.
    """

    patient_id: str
    first_name: str
    last_name: str
    dob: str  # ISO date, e.g. "1988-09-18"
    message: str  # the request text (intake's request.details or transcript)
    task_id: Optional[str] = None


class MessageRelayResult(BaseModel):
    patient: Dict[str, Any]
    worth_relaying: bool
    route: Literal["physician", "staff", "none"]
    status: Literal["pending_approval", "rejected"]
    agent_summary: str
    agent_checks: Dict[str, Any]
    flagged_reason: Optional[str] = None
    proposed_action: Optional[Dict[str, Any]] = None
