from __future__ import annotations

import pytest

from scheduling_eligibility.claude_summary import generate_agent_summary
from scheduling_eligibility.errors import MissingAnthropicAPIKeyError


class FakeTextBlock:
    type = "text"

    def __init__(self, text: str):
        self.text = text


class FakeMessage:
    def __init__(self, text: str):
        self.content = [FakeTextBlock(text)]


class FakeMessagesAPI:
    def __init__(self, text: str):
        self._text = text
        self.last_call: dict | None = None

    def create(self, **kwargs):
        self.last_call = kwargs
        return FakeMessage(self._text)


class FakeAnthropicClient:
    def __init__(self, text: str):
        self.messages = FakeMessagesAPI(text)


def test_missing_api_key_raises_a_stable_error():
    with pytest.raises(MissingAnthropicAPIKeyError) as exc_info:
        generate_agent_summary({"foo": "bar"}, api_key="")

    assert exc_info.value.code == "missing_anthropic_api_key"
    assert exc_info.value.status_code == 500


def test_generate_agent_summary_extracts_text_blocks():
    client = FakeAnthropicClient("Eligible to proceed, no conflicts found.")

    summary = generate_agent_summary({"foo": "bar"}, api_key="test-key", client=client)

    assert summary == "Eligible to proceed, no conflicts found."
    assert client.messages.last_call["model"]
    assert "bar" in client.messages.last_call["messages"][0]["content"]
