from __future__ import annotations

import json
from pathlib import Path

from orchestrator.main_loop import run_directory


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


def test_robert_conflict_gets_alternative_slot():
    result = next(
        item
        for item in run_directory(DEMO_INPUT)
        if Path(item["source_file"]).name == "04_robert_martinez_reschedule_conflict.intake.json"
    )

    assert result["agent_checks"]["scheduling_eligibility"]["conflict"] is True
    assert result["proposed_action"]["new_start"] == "2026-06-25T09:00:00+00:00"


def test_orchestrator_output_is_json_serializable():
    json.dumps(run_directory(DEMO_INPUT))
