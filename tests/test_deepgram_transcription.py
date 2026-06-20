from __future__ import annotations

import asyncio
import json
from pathlib import Path

import httpx
import pytest

from transcription.deepgram_client import (
    DEEPGRAM_DEFAULT_PARAMS,
    DEEPGRAM_LISTEN_URL,
    infer_audio_content_type,
    request_deepgram_transcription,
)
from transcription.errors import InvalidAudioError, MissingAPIKeyError, ProviderTranscriptionError
from transcription.schemas import to_plain_dict
from transcription.service import normalize_deepgram_response


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "deepgram_pre_recorded_success.json"
CONTRACT_PATH = ROOT / "backend" / "api" / "contracts" / "transcription_response.example.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_deepgram_response_normalization_matches_contract_fixture():
    raw = load_json(FIXTURE_PATH)
    expected = load_json(CONTRACT_PATH)

    normalized = to_plain_dict(normalize_deepgram_response(raw))

    assert normalized == expected


def test_content_type_inference_keeps_browser_recorded_audio_portable():
    assert infer_audio_content_type("voicemail.webm") == "audio/webm"
    assert infer_audio_content_type("voicemail.wav") == "audio/wav"
    assert infer_audio_content_type("voicemail.mp3") == "audio/mpeg"


def test_missing_api_key_returns_stable_error():
    with pytest.raises(MissingAPIKeyError) as exc_info:
        asyncio.run(
            request_deepgram_transcription(
                b"audio",
                filename="sample.wav",
                content_type="audio/wav",
                api_key="",
            )
        )

    assert exc_info.value.code == "missing_api_key"
    assert exc_info.value.status_code == 500
    assert str(exc_info.value) == "Deepgram API key not configured."


def test_empty_audio_is_rejected_before_provider_call():
    with pytest.raises(InvalidAudioError) as exc_info:
        asyncio.run(
            request_deepgram_transcription(
                b"",
                filename="sample.wav",
                content_type="audio/wav",
                api_key="test-key",
            )
        )

    assert exc_info.value.code == "invalid_audio"
    assert exc_info.value.status_code == 400


def test_provider_failure_maps_to_safe_error_shape():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"err_msg": "provider unavailable"})

    transport = httpx.MockTransport(handler)

    with pytest.raises(ProviderTranscriptionError) as exc_info:
        async def run_request() -> None:
            async with httpx.AsyncClient(transport=transport) as client:
                await request_deepgram_transcription(
                    b"audio",
                    filename="sample.wav",
                    content_type="audio/wav",
                    api_key="test-key",
                    client=client,
                )

        asyncio.run(run_request())

    assert exc_info.value.code == "provider_error"
    assert exc_info.value.status_code == 502
    assert exc_info.value.provider_status_code == 503
    assert str(exc_info.value) == "provider unavailable"


def test_deepgram_request_uses_stable_endpoint_and_options():
    raw = load_json(FIXTURE_PATH)
    seen: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url.copy_with(query=None))
        seen["params"] = dict(request.url.params)
        seen["authorization"] = request.headers.get("authorization")
        seen["content_type"] = request.headers.get("content-type")
        seen["body"] = request.content
        return httpx.Response(200, json=raw)

    async def run_request() -> dict:
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            return await request_deepgram_transcription(
                b"audio-bytes",
                filename="sample.wav",
                content_type="audio/wav",
                api_key="test-key",
                client=client,
            )

    result = asyncio.run(run_request())

    assert result == raw
    assert seen["url"] == DEEPGRAM_LISTEN_URL
    assert seen["params"] == DEEPGRAM_DEFAULT_PARAMS
    assert seen["authorization"] == "Token test-key"
    assert seen["content_type"] == "audio/wav"
    assert seen["body"] == b"audio-bytes"

