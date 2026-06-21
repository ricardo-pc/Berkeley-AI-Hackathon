from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class BookingRequest(BaseModel):
    """Input to the scheduler agent: who, and the pre-approved slot to write."""

    patient_id: str  # canonical lookup key (uniform with the eligibility agents)
    first_name: str
    last_name: str
    dob: str  # ISO date, e.g. "1978-03-12"

    # The pre-approved slot (decided upstream by the eligibility step).
    provider_id: str
    start_time: datetime
    end_time: datetime
    visit_type: str = "follow_up"

    # The existing appointment being moved; it gets marked "rescheduled".
    cancel_appointment_id: Optional[str] = None

    task_id: Optional[str] = None
