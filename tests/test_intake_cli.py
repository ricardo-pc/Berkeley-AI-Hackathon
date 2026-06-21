from __future__ import annotations

import json
from pathlib import Path

from agents.intake import cli
from agents.intake.schemas import IntakeExtraction


def test_intake_cli_prints_extracted_json(monkeypatch, tmp_path, capsys):
    stt_path = tmp_path / "stt.json"
    output_path = tmp_path / "intake.json"
    stt_path.write_text(json.dumps({"transcript": "Linda Chen has Kaiser and wants to reschedule."}), encoding="utf-8")

    def fake_run_intake_extraction(stt_json):
        assert stt_json == {"transcript": "Linda Chen has Kaiser and wants to reschedule."}
        return IntakeExtraction(
            first_name="Linda",
            last_name="Chen",
            insurance_plan="Kaiser",
            request={
                "type": "reschedule",
                "details": "Patient wants to reschedule.",
            },
            transcript=stt_json["transcript"],
        )

    monkeypatch.setattr(cli, "run_intake_extraction", fake_run_intake_extraction)

    exit_code = cli.main([str(stt_path), "--pretty", "--output", str(output_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out)["first_name"] == "Linda"
    assert json.loads(output_path.read_text(encoding="utf-8"))["request"]["type"] == "reschedule"


def test_intake_cli_reports_invalid_json_file(capsys):
    exit_code = cli.main(["does-not-exist.json"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert json.loads(captured.err)["error"]["code"] == "invalid_stt_json_file"
