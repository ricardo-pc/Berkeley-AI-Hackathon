from __future__ import annotations

import mimetypes
import os
from pathlib import Path
from typing import Any

import httpx

from .errors import InvalidAudioError, MissingAPIKeyError, ProviderTranscriptionError

try:
    from dotenv import find_dotenv, load_dotenv
except ImportError:  # pragma: no cover - python-dotenv is listed in requirements.
    find_dotenv = None
    load_dotenv = None


DEEPGRAM_LISTEN_URL = "https://api.deepgram.com/v1/listen"
DEEPGRAM_DEFAULT_PARAMS = {
    "model": "nova-3",
    "smart_format": "true",
    "punctuate": "true",
    "numerals": "true",
    "utterances": "true",
}


def load_environment() -> None:
    if not find_dotenv or not load_dotenv:
        return
    env_path = find_dotenv(usecwd=True)
    if env_path:
        load_dotenv(env_path)


def get_deepgram_api_key(api_key: str | None = None) -> str:
    load_environment()
    resolved = api_key if api_key is not None else os.getenv("DEEPGRAM_API_KEY")
    if not resolved:
        raise MissingAPIKeyError()
    return resolved


def infer_audio_content_type(filename: str | None, content_type: str | None = None) -> str:
    if content_type and content_type != "application/octet-stream":
        return content_type

    suffix = Path(filename or "").suffix.lower()
    overrides = {
        ".m4a": "audio/mp4",
        ".mp3": "audio/mpeg",
        ".ogg": "audio/ogg",
        ".opus": "audio/ogg",
        ".wav": "audio/wav",
        ".webm": "audio/webm",
    }
    if suffix in overrides:
        return overrides[suffix]

    guessed, _ = mimetypes.guess_type(filename or "")
    return guessed or "application/octet-stream"


async def request_deepgram_transcription(
    audio_bytes: bytes,
    filename: str | None,
    content_type: str | None = None,
    *,
    api_key: str | None = None,
    client: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    if not audio_bytes:
        raise InvalidAudioError()

    headers = {
        "Authorization": f"Token {get_deepgram_api_key(api_key)}",
        "Content-Type": infer_audio_content_type(filename, content_type),
    }

    async def post_with(active_client: httpx.AsyncClient) -> httpx.Response:
        return await active_client.post(
            DEEPGRAM_LISTEN_URL,
            params=DEEPGRAM_DEFAULT_PARAMS,
            content=audio_bytes,
            headers=headers,
        )

    try:
        if client is not None:
            response = await post_with(client)
        else:
            async with httpx.AsyncClient(timeout=90.0) as active_client:
                response = await post_with(active_client)
    except httpx.HTTPError as exc:
        raise ProviderTranscriptionError("Could not reach Deepgram speech-to-text service.") from exc

    if response.status_code >= 400:
        raise ProviderTranscriptionError(
            _provider_error_message(response),
            provider_status_code=response.status_code,
        )

    try:
        return response.json()
    except ValueError as exc:
        raise ProviderTranscriptionError("Deepgram returned an invalid JSON response.") from exc


def _provider_error_message(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        payload = {}

    message = payload.get("err_msg") or payload.get("message") or payload.get("error")
    if not message:
        message = "Deepgram speech-to-text request failed."
    return str(message)

