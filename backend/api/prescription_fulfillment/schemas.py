from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class RefillRequest(BaseModel):
    """Input to the prescription fulfillment agent: who, and the pre-approved refill to write.

    Field names mirror prescription_eligibility's proposed_action so a CHW-approval
    handler can pass that dict straight through.
    """

    patient_id: str  # canonical lookup key (uniform with the eligibility agents)
    first_name: str
    last_name: str
    dob: str  # ISO date, e.g. "1978-03-12"

    medication_name: str
    dosage: str
    instructions: str
    provider_id: str

    task_id: Optional[str] = None
