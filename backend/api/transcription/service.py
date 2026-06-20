from __future__ import annotations

from typing import Any
from uuid import uuid4

from .deepgram_client import request_deepgram_transcription
from .schemas import TranscriptionResponse, Utterance


async def transcribe_audio(
    audio_bytes: bytes,
    filename: str | None,
    content_type: str | None = None,
) -> TranscriptionResponse:
    raw_response = await request_deepgram_transcription(audio_bytes, filename, content_type)
    return normalize_deepgram_response(raw_response)


def normalize_deepgram_response(raw_response: dict[str, Any]) -> TranscriptionResponse:
    metadata = raw_response.get("metadata") or {}
    results = raw_response.get("results") or {}
    alternative = _first_alternative(results)
    provider_request_id = metadata.get("request_id")

    return TranscriptionResponse(
        id=_transcription_id(provider_request_id),
        transcript=str(alternative.get("transcript") or ""),
        confidence=_as_float(alternative.get("confidence")),
        duration=_as_float(metadata.get("duration")),
        utterances=[_normalize_utterance(utterance) for utterance in results.get("utterances") or []],
        provider_request_id=str(provider_request_id) if provider_request_id else None,
        raw_provider_response=raw_response,
    )


def _first_alternative(results: dict[str, Any]) -> dict[str, Any]:
    channels = results.get("channels") or []
    if not channels:
        return {}

    alternatives = channels[0].get("alternatives") or []
    if not alternatives:
        return {}

    return alternatives[0] or {}


def _normalize_utterance(utterance: dict[str, Any]) -> Utterance:
    return Utterance(
        id=str(utterance["id"]) if utterance.get("id") is not None else None,
        start=_as_float(utterance.get("start")),
        end=_as_float(utterance.get("end")),
        confidence=_as_float(utterance.get("confidence")),
        channel=_as_int(utterance.get("channel")),
        speaker=_as_int(utterance.get("speaker")),
        transcript=str(utterance.get("transcript") or ""),
        words=list(utterance.get("words") or []),
    )


def _transcription_id(provider_request_id: Any) -> str:
    if provider_request_id:
        return f"tr_{provider_request_id}"
    return f"tr_{uuid4().hex}"


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

