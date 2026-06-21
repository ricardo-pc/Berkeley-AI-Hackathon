from __future__ import annotations

from typing import Any

from .errors import InvalidSTTPayloadError


def extract_transcript_from_stt_json(stt_json: dict[str, Any]) -> str:
    normalized_transcript = stt_json.get("transcript")
    if isinstance(normalized_transcript, str) and normalized_transcript.strip():
        return normalized_transcript.strip()

    channels = ((stt_json.get("results") or {}).get("channels") or [])
    if channels:
        alternatives = channels[0].get("alternatives") or []
        if alternatives:
            transcript = alternatives[0].get("transcript")
            if isinstance(transcript, str) and transcript.strip():
                return transcript.strip()

    utterances = (stt_json.get("results") or {}).get("utterances") or stt_json.get("utterances") or []
    utterance_text = " ".join(
        utterance.get("transcript", "").strip()
        for utterance in utterances
        if isinstance(utterance, dict) and utterance.get("transcript")
    ).strip()
    if utterance_text:
        return utterance_text

    raise InvalidSTTPayloadError()

