from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel


class PrescriptionEligibilityRequest(BaseModel):
    patient_id: str
    medication_name: str
    dosage: str
    instructions: str
    task_id: Optional[str] = None


class PrescriptionEligibilityResult(BaseModel):
    eligible: bool
    status: Literal["pending_approval", "escalated"]
    flagged_reason: Optional[str] = None
    checks: Dict[str, Any]
    proposed_action: Optional[Dict[str, Any]] = None
