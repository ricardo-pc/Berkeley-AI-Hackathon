from __future__ import annotations

import asyncio

import httpx

from .config import TelephonyConfig
from .errors import MissingTelephonyCredentialsError, RecordingDownloadError

_CONTENT_TYPE_BY_FORMAT = {
    "wav": "audio/wav",
    "mp3": "audio/mpeg",
}


def build_recording_media_url(recording_url: str, recording_format: str) -> str:
    """Compatibility recording URLs usually accept a format extension."""
    if recording_url.endswith((".wav", ".mp3")):
        return recording_url
    fmt = recording_format if recording_format in _CONTENT_TYPE_BY_FORMAT else "wav"
    return f"{recording_url}.{fmt}"


async def download_recording(
    recording_url: str,
    config: TelephonyConfig,
    *,
    client: httpx.AsyncClient | None = None,
    max_attempts: int = 3,
    retry_delay_seconds: float = 1.0,
) -> tuple[bytes, str, str]:
    """Download a provider recording, returning ``(audio_bytes, content_type, filename)``.

    Providers occasionally answer a freshly-completed recording with a 404 for
    a moment, so we retry a couple of times before giving up.
    """
    if not (config.account_sid and config.auth_token):
        raise MissingTelephonyCredentialsError(config.provider)

    media_url = build_recording_media_url(recording_url, config.recording_format)
    fmt = "mp3" if media_url.endswith(".mp3") else "wav"
    content_type = _CONTENT_TYPE_BY_FORMAT[fmt]
    filename = media_url.rsplit("/", 1)[-1]
    auth = (config.account_sid, config.auth_token)

    async def fetch(active_client: httpx.AsyncClient) -> bytes:
        last_status = None
        for attempt in range(max_attempts):
            response = await active_client.get(media_url, auth=auth, follow_redirects=True)
            if response.status_code == 200 and response.content:
                return response.content
            last_status = response.status_code
            if response.status_code == 404 and attempt < max_attempts - 1:
                await asyncio.sleep(retry_delay_seconds)
                continue
            break
        raise RecordingDownloadError(
            f"{config.provider.title()} returned status {last_status} when downloading {media_url}."
        )

    try:
        if client is not None:
            audio_bytes = await fetch(client)
        else:
            async with httpx.AsyncClient(timeout=60.0) as active_client:
                audio_bytes = await fetch(active_client)
    except httpx.HTTPError as exc:
        raise RecordingDownloadError(
            f"Could not reach {config.provider.title()} to download the recording."
        ) from exc

    return audio_bytes, content_type, filename
