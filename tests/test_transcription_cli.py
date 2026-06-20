from __future__ import annotations

import json
from pathlib import Path

from transcription import cli
from transcription.service import normalize_deepgram_response


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "deepgram_pre_recorded_success.json"
CONTRACT_PATH = ROOT / "backend" / "api" / "contracts" / "transcription_response.example.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_cli_prints_same_contract_as_api(monkeypatch, tmp_path, capsys):
    raw = load_json(FIXTURE_PATH)
    expected = load_json(CONTRACT_PATH)
    audio_path = tmp_path / "sample.wav"
    output_path = tmp_path / "result.json"
    audio_path.write_bytes(b"audio")

    async def fake_transcribe_audio(audio_bytes: bytes, filename: str | None, content_type: str | None = None):
        assert audio_bytes == b"audio"
        assert filename == "sample.wav"
        assert content_type == "audio/wav"
        return normalize_deepgram_response(raw)

    monkeypatch.setattr(cli, "transcribe_audio", fake_transcribe_audio)

    exit_code = cli.main([str(audio_path), "--pretty", "--output", str(output_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out) == expected
    assert json.loads(output_path.read_text(encoding="utf-8")) == expected


def test_cli_missing_file_uses_stable_error(capsys):
    exit_code = cli.main(["does-not-exist.wav"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert json.loads(captured.err) == {
        "error": {
            "code": "invalid_audio",
            "message": "Audio file not found: does-not-exist.wav",
        }
    }

