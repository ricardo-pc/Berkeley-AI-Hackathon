from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


REFERENCE_NOW = datetime(2026, 6, 20, tzinfo=timezone.utc)

PROVIDER_AVAILABILITY = {
    "mon": ["09:00", "17:00"],
    "tue": ["09:00", "17:00"],
    "wed": ["09:00", "17:00"],
    "thu": ["09:00", "17:00"],
    "fri": ["09:00", "17:00"],
}

PATIENTS: list[dict[str, Any]] = [
    {
        "id": "a1b2c3d4-0001-0001-0001-000000000001",
        "first_name": "Maria",
        "last_name": "Gonzalez",
        "date_of_birth": "1978-03-12",
        "phone": "415-555-0101",
        "insurance_plan": "Blue Cross PPO",
        "insurance_valid": True,
    },
    {
        "id": "a1b2c3d4-0002-0002-0002-000000000002",
        "first_name": "James",
        "last_name": "Okafor",
        "date_of_birth": "1965-07-24",
        "phone": "510-555-0182",
        "insurance_plan": "Aetna HMO",
        "insurance_valid": True,
    },
    {
        "id": "a1b2c3d4-0003-0003-0003-000000000003",
        "first_name": "Linda",
        "last_name": "Chen",
        "date_of_birth": "1990-11-05",
        "phone": "628-555-0193",
        "insurance_plan": "Kaiser Permanente",
        "insurance_valid": False,
    },
    {
        "id": "a1b2c3d4-0004-0004-0004-000000000004",
        "first_name": "Robert",
        "last_name": "Martinez",
        "date_of_birth": "1952-01-30",
        "phone": "415-555-0174",
        "insurance_plan": "United Healthcare",
        "insurance_valid": True,
    },
    {
        "id": "a1b2c3d4-0005-0005-0005-000000000005",
        "first_name": "Priya",
        "last_name": "Sharma",
        "date_of_birth": "1988-09-18",
        "phone": "510-555-0165",
        "insurance_plan": "Blue Cross PPO",
        "insurance_valid": True,
    },
]

PROVIDERS: list[dict[str, Any]] = [
    {
        "id": "b1b2c3d4-0001-0001-0001-000000000001",
        "name": "Dr. Sarah Lee",
        "availability": PROVIDER_AVAILABILITY,
    },
    {
        "id": "b1b2c3d4-0002-0002-0002-000000000002",
        "name": "Dr. James Patel",
        "availability": {
            "mon": ["08:00", "16:00"],
            "wed": ["08:00", "16:00"],
            "fri": ["08:00", "13:00"],
        },
    },
]

APPOINTMENTS: list[dict[str, Any]] = [
    {
        "id": "c1b2c3d4-0001-0001-0001-000000000001",
        "patient_id": "a1b2c3d4-0001-0001-0001-000000000001",
        "provider_id": "b1b2c3d4-0001-0001-0001-000000000001",
        "start_time": "2026-01-10T10:00:00+00:00",
        "end_time": "2026-01-10T10:30:00+00:00",
        "status": "scheduled",
    },
    {
        "id": "c1b2c3d4-0002-0002-0002-000000000002",
        "patient_id": "a1b2c3d4-0001-0001-0001-000000000001",
        "provider_id": "b1b2c3d4-0001-0001-0001-000000000001",
        "start_time": "2026-09-15T10:00:00+00:00",
        "end_time": "2026-09-15T10:30:00+00:00",
        "status": "scheduled",
    },
    {
        "id": "c1b2c3d4-0003-0003-0003-000000000003",
        "patient_id": "a1b2c3d4-0002-0002-0002-000000000002",
        "provider_id": "b1b2c3d4-0002-0002-0002-000000000002",
        "start_time": "2024-11-20T09:00:00+00:00",
        "end_time": "2024-11-20T09:30:00+00:00",
        "status": "scheduled",
    },
    {
        "id": "c1b2c3d4-0004-0004-0004-000000000004",
        "patient_id": "a1b2c3d4-0004-0004-0004-000000000004",
        "provider_id": "b1b2c3d4-0001-0001-0001-000000000001",
        "start_time": "2026-06-24T15:00:00+00:00",
        "end_time": "2026-06-24T15:30:00+00:00",
        "status": "scheduled",
    },
    {
        "id": "c1b2c3d4-0005-0005-0005-000000000005",
        "patient_id": "a1b2c3d4-0005-0005-0005-000000000005",
        "provider_id": "b1b2c3d4-0001-0001-0001-000000000001",
        "start_time": "2026-07-08T11:00:00+00:00",
        "end_time": "2026-07-08T11:30:00+00:00",
        "status": "scheduled",
    },
]

PRESCRIPTIONS: list[dict[str, Any]] = [
    {
        "patient_id": "a1b2c3d4-0001-0001-0001-000000000001",
        "provider_id": "b1b2c3d4-0001-0001-0001-000000000001",
        "medication_name": "Lisinopril",
        "dosage": "10mg",
        "instructions": "once daily with food",
        "active": True,
    },
    {
        "patient_id": "a1b2c3d4-0001-0001-0001-000000000001",
        "provider_id": "b1b2c3d4-0001-0001-0001-000000000001",
        "medication_name": "Amlodipine",
        "dosage": "5mg",
        "instructions": "once daily",
        "active": True,
    },
    {
        "patient_id": "a1b2c3d4-0002-0002-0002-000000000002",
        "provider_id": "b1b2c3d4-0002-0002-0002-000000000002",
        "medication_name": "Metformin",
        "dosage": "500mg",
        "instructions": "twice daily with meals",
        "active": True,
    },
    {
        "patient_id": "a1b2c3d4-0005-0005-0005-000000000005",
        "provider_id": "b1b2c3d4-0001-0001-0001-000000000001",
        "medication_name": "Sertraline",
        "dosage": "50mg",
        "instructions": "once daily in the morning",
        "active": True,
    },
]

