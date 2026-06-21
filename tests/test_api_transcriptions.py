from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

import main
from transcription.errors import MissingAPIKeyError, ProviderTranscriptionError
from transcription.schemas import to_plain_dict
from transcription.service import normalize_deepgram_response


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "deepgram_pre_recorded_success.json"
CONTRACT_PATH = ROOT / "backend" / "api" / "contracts" / "transcription_response.example.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_health_route():
    client = TestClient(main.app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_transcriptions_route_returns_contract(monkeypatch):
    expected = load_json(CONTRACT_PATH)
    raw = load_json(FIXTURE_PATH)

    async def fake_transcribe_audio(audio_bytes: bytes, filename: str | None, content_type: str | None = None):
        assert audio_bytes == b"audio"
        assert filename == "sample.wav"
        assert content_type == "audio/wav"
        return normalize_deepgram_response(raw)

    monkeypatch.setattr(main, "transcribe_audio", fake_transcribe_audio)
    client = TestClient(main.app)

    response = client.post(
        "/api/transcriptions",
        files={"file": ("sample.wav", b"audio", "audio/wav")},
    )

    assert response.status_code == 200
    assert response.json() == expected


def test_api_transcriptions_text_route_returns_compact_transcript(monkeypatch):
    raw = load_json(FIXTURE_PATH)

    async def fake_transcribe_audio(audio_bytes: bytes, filename: str | None, content_type: str | None = None):
        result = normalize_deepgram_response(raw)
        result.transcript = "Line one.\nLine two.\n\nLine three."
        return result

    monkeypatch.setattr(main, "transcribe_audio", fake_transcribe_audio)
    client = TestClient(main.app)

    response = client.post(
        "/api/transcriptions/text",
        files={"file": ("sample.wav", b"audio", "audio/wav")},
    )

    assert response.status_code == 200
    assert response.json() == {"transcript": "Line one. Line two. Line three."}


def test_api_transcriptions_text_route_requires_file_field():
    client = TestClient(main.app)

    response = client.post(
        "/api/transcriptions/text",
        files={"audio": ("sample.wav", b"audio", "audio/wav")},
    )

    assert response.status_code == 400
    assert response.json() == {
        "error": {
            "code": "invalid_audio",
            "message": "A non-empty audio file is required in form field 'file'.",
        }
    }


def test_mock_james_text_route_returns_sample_transcript():
    client = TestClient(main.app)

    response = client.get("/api/mock/transcriptions/james/text")

    assert response.status_code == 200
    assert response.json() == {
        "transcript": (
            "Hey, this is James Okafor. My birthday is July 24, 1965. I need a refill on my "
            "Metformin 500 milligrams, twice daily with meals. I have Aetna HMO insurance. "
            "You can reach me at 510-555-0182."
        )
    }


def test_mock_james_verbose_route_returns_normalized_sample():
    client = TestClient(main.app)

    response = client.get("/api/mock/transcriptions/james")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "tr_mock_dg_james_refill_old_visit"
    assert payload["transcript"].startswith("Hey, this is James Okafor.")
    assert payload["duration"] == 11.9
    assert payload["provider"] == "deepgram"


def test_api_transcriptions_route_requires_file_field():
    client = TestClient(main.app)

    response = client.post(
        "/api/transcriptions",
        files={"audio": ("sample.wav", b"audio", "audio/wav")},
    )

    assert response.status_code == 400
    assert response.json() == {
        "error": {
            "code": "invalid_audio",
            "message": "A non-empty audio file is required in form field 'file'.",
        }
    }


def test_api_missing_key_error_shape_is_stable(monkeypatch):
    async def fake_transcribe_audio(audio_bytes: bytes, filename: str | None, content_type: str | None = None):
        raise MissingAPIKeyError()

    monkeypatch.setattr(main, "transcribe_audio", fake_transcribe_audio)
    client = TestClient(main.app)

    response = client.post(
        "/api/transcriptions",
        files={"file": ("sample.wav", b"audio", "audio/wav")},
    )

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "missing_api_key",
            "message": "Deepgram API key not configured.",
        }
    }


def test_api_provider_failure_error_shape_is_stable(monkeypatch):
    async def fake_transcribe_audio(audio_bytes: bytes, filename: str | None, content_type: str | None = None):
        raise ProviderTranscriptionError("Deepgram speech-to-text request failed.", provider_status_code=503)

    monkeypatch.setattr(main, "transcribe_audio", fake_transcribe_audio)
    client = TestClient(main.app)

    response = client.post(
        "/api/transcriptions",
        files={"file": ("sample.wav", b"audio", "audio/wav")},
    )

    assert response.status_code == 502
    assert response.json() == {
        "error": {
            "code": "provider_error",
            "message": "Deepgram speech-to-text request failed.",
        }
    }


def test_transcription_response_contract_keeps_required_keys():
    contract = load_json(CONTRACT_PATH)

    assert set(contract) == {
        "id",
        "transcript",
        "confidence",
        "duration",
        "utterances",
        "provider",
        "provider_request_id",
        "raw_provider_response",
    }
    assert contract["provider"] == "deepgram"
