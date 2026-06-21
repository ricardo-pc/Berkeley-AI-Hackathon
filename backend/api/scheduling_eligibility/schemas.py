from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel


class ScheduleEligibilityRequest(BaseModel):
    patient_id: str
    provider_id: str
    requested_start: datetime
    requested_end: datetime
    cancel_appointment_id: Optional[str] = None
    task_id: Optional[str] = None


class ScheduleEligibilityResult(BaseModel):
    eligible: bool
    status: Literal["pending_approval", "escalated"]
    flagged_reason: Optional[str] = None
    agent_checks: Dict[str, Any]
    agent_summary: str
    suggested_timeslot: Optional[Dict[str, Any]] = None
    proposed_action: Optional[Dict[str, Any]] = None
