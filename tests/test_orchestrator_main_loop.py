from __future__ import annotations

import json
from pathlib import Path

from orchestrator.main_loop import run_directory, run_intake


DEMO_INPUT = Path(__file__).resolve().parents[1] / "demo" / "intake_output"


def test_orchestrator_runs_demo_intake_outputs():
    results = run_directory(DEMO_INPUT)

    by_file = {Path(result["source_file"]).name: result for result in results}

    assert by_file["01_maria_gonzalez_refill_valid.intake.json"]["status"] == "pending_approval"
    assert by_file["02_james_okafor_refill_old_visit.intake.json"]["status"] == "escalated"
    assert by_file["03_linda_chen_reschedule_invalid_insurance.intake.json"]["status"] == "escalated"
    assert by_file["04_robert_martinez_reschedule_conflict.intake.json"]["status"] == "pending_approval"
    assert by_file["05_priya_sharma_message_relay_adverse_reaction.intake.json"]["status"] == "pending_approval"
    assert by_file["06_unknown_patient_refill_not_in_db.intake.json"]["status"] == "escalated"
    assert by_file["07_missing_dob_and_insurance_reschedule.intake.json"]["status"] == "escalated"
    assert by_file["09_maria_gonzalez_dosage_mismatch.intake.json"]["status"] == "escalated"

    emergency = by_file["08_emergency_symptoms_escalation.intake.json"]
    assert emergency["status"] == "escalated"
    assert emergency["task_type"] == "escalate"
    assert "emergency" in emergency["flagged_reason"].lower()
    assert emergency["agent_checks"]["triage"]["emergency_signal"] is True


def test_emergency_phrase_bypasses_automation_regardless_of_request_type():
    """A refill call that also mentions chest pain must escalate before prescription logic runs."""
    intake = {
        "first_name": "Maria",
        "last_name": "Gonzalez",
        "date_of_birth": "1978-03-12",
        "phone_number": "415-555-0101",
        "insurance_plan": "Blue Cross PPO",
        "request": {"type": "refill", "details": "refill request", "orders": ["Lisinopril"], "preferred_times": []},
        "missing_fields": [],
        "transcript": "I need my Lisinopril refilled, but also I'm having chest pain right now.",
    }

    result = run_intake(intake)

    assert result["status"] == "escalated"
    assert result["task_type"] == "escalate"
    assert "emergency" in result["flagged_reason"].lower()
    # Should short-circuit before any prescription-specific checks run.
    assert "prescription" not in result["agent_checks"]


def test_robert_conflict_gets_alternative_slot():
    result = next(
        item
        for item in run_directory(DEMO_INPUT)
        if Path(item["source_file"]).name == "04_robert_martinez_reschedule_conflict.intake.json"
    )

    assert result["agent_checks"]["scheduling_eligibility"]["conflict"] is True
    assert result["agent_checks"]["scheduling_eligibility"]["alternative_slot_found"] is True
    # The real Scheduling Agent now finds the soonest open slot -- same day,
    # right after the conflicting appointment ends -- rather than jumping to
    # the next day.
    assert result["proposed_action"]["new_start"] == "2026-06-24T15:30:00+00:00"


def test_orchestrator_output_is_json_serializable():
    json.dumps(run_directory(DEMO_INPUT))
