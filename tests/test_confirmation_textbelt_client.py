from __future__ import annotations

import httpx
import pytest

from confirmation.errors import MissingTextbeltConfigError, TextbeltSendError
from confirmation.textbelt_client import TEXTBELT_URL, send_sms


def test_missing_api_key_raises_a_stable_error():
    with pytest.raises(MissingTextbeltConfigError) as exc_info:
        send_sms("+15105550101", "hi", api_key="")

    assert exc_info.value.code == "missing_textbelt_config"
    assert exc_info.value.status_code == 500


def test_successful_send_returns_normalized_result():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"success": True, "textId": "abc123", "quotaRemaining": 49})

    client = httpx.Client(transport=httpx.MockTransport(handler))

    result = send_sms("+15105550101", "hi there", api_key="test-key", client=client)

    assert result == {
        "sid": "abc123",
        "status": "queued",
        "to": "+15105550101",
        "body": "hi there",
        "quota_remaining": 49,
    }


def test_failed_send_raises_with_textbelt_error_message():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"success": False, "error": "Invalid phone number"})

    client = httpx.Client(transport=httpx.MockTransport(handler))

    with pytest.raises(TextbeltSendError) as exc_info:
        send_sms("+1bad", "hi", api_key="test-key", client=client)

    assert "Invalid phone number" in str(exc_info.value)
    assert exc_info.value.code == "textbelt_send_failed"


def test_posts_to_the_stable_textbelt_endpoint():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["body"] = request.content
        return httpx.Response(200, json={"success": True, "textId": "abc123", "quotaRemaining": 1})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    send_sms("+15105550101", "hi", api_key="test-key", client=client)

    assert seen["url"] == TEXTBELT_URL
    assert b"phone=" in seen["body"]
    assert b"key=test-key" in seen["body"]
