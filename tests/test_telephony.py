from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi.testclient import TestClient

import main
from telephony.config import TelephonyConfig, get_telephony_config
from telephony.recordings import build_recording_media_url, download_recording
from telephony.twiml import build_goodbye_twiml, build_voicemail_twiml
from transcription.schemas import TranscriptionResponse


def make_config(**overrides: Any) -> TelephonyConfig:
    base = dict(
        provider="twilio",
        account_sid="AC_test",
        auth_token="token_test",
        signing_key="token_test",
        validate_signature=False,
        public_base_url=None,
        recording_format="wav",
        greeting=None,
        max_recording_seconds=120,
    )
    base.update(overrides)
    return TelephonyConfig(**base)


def use_config(monkeypatch, config: TelephonyConfig) -> None:
    monkeypatch.setattr(main, "get_telephony_config", lambda: config)


# --- TwiML rendering --------------------------------------------------------


def test_voicemail_twiml_records_with_callbacks():
    twiml = build_voicemail_twiml(
        action_url="https://host.test/api/telephony/recording-complete",
        recording_status_callback_url="https://host.test/api/telephony/recording",
        max_length_seconds=90,
    )

    assert "<Record" in twiml
    assert 'action="https://host.test/api/telephony/recording-complete"' in twiml
    assert 'recordingStatusCallback="https://host.test/api/telephony/recording"' in twiml
    assert 'maxLength="90"' in twiml


def test_goodbye_twiml_hangs_up():
    twiml = build_goodbye_twiml()

    assert "<Hangup" in twiml


def test_recording_media_url_appends_extension():
    base = "https://api.twilio.com/2010-04-01/Accounts/AC/Recordings/RE123"

    assert build_recording_media_url(base, "wav") == f"{base}.wav"
    assert build_recording_media_url(base, "mp3") == f"{base}.mp3"
    assert build_recording_media_url(f"{base}.wav", "mp3") == f"{base}.wav"


def test_signalwire_env_config(monkeypatch):
    monkeypatch.setenv("TELEPHONY_PROVIDER", "signalwire")
    monkeypatch.setenv("SIGNALWIRE_PROJECT_ID", "project_test")
    monkeypatch.setenv("SIGNALWIRE_API_TOKEN", "api_token_test")
    monkeypatch.setenv("SIGNALWIRE_SIGNING_KEY", "signing_key_test")
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://host.test")

    config = get_telephony_config()

    assert config.provider == "signalwire"
    assert config.account_sid == "project_test"
    assert config.auth_token == "api_token_test"
    assert config.signing_key == "signing_key_test"
    assert config.public_base_url == "https://host.test"


def test_signalwire_recording_download_uses_project_auth():
    class Response:
        status_code = 200
        content = b"audio-bytes"

    class Client:
        seen: dict[str, Any] = {}

        async def get(self, url, auth, follow_redirects=False):
            self.seen = {
                "url": url,
                "auth": auth,
                "follow_redirects": follow_redirects,
            }
            return Response()

    client = Client()
    config = make_config(
        provider="signalwire",
        account_sid="project_test",
        auth_token="api_token_test",
        signing_key="signing_key_test",
    )

    audio_bytes, content_type, filename = asyncio.run(
        download_recording(
            "https://space.signalwire.com/api/laml/.../Recordings/RE9",
            config,
            client=client,
        )
    )

    assert audio_bytes == b"audio-bytes"
    assert content_type == "audio/wav"
    assert filename == "RE9.wav"
    assert client.seen == {
        "url": "https://space.signalwire.com/api/laml/.../Recordings/RE9.wav",
        "auth": ("project_test", "api_token_test"),
        "follow_redirects": True,
    }


# --- Voice webhook ----------------------------------------------------------


def test_voice_webhook_returns_record_twiml(monkeypatch):
    use_config(monkeypatch, make_config(public_base_url="https://host.test"))
    client = TestClient(main.app)

    response = client.post("/api/telephony/voice", data={"CallSid": "CA1"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")
    assert "<Record" in response.text
    assert "https://host.test/api/telephony/recording" in response.text
    assert "https://host.test/api/telephony/recording-complete" in response.text


def test_signalwire_voice_webhook_returns_compatible_record_cxml(monkeypatch):
    use_config(
        monkeypatch,
        make_config(
            provider="signalwire",
            account_sid="project_test",
            auth_token="api_token_test",
            signing_key="signing_key_test",
            public_base_url="https://host.test",
        ),
    )
    client = TestClient(main.app)

    response = client.post("/api/telephony/voice", data={"CallSid": "signalwire-call"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")
    assert "<Record" in response.text
    assert "https://host.test/api/telephony/recording" in response.text
    assert "https://host.test/api/telephony/recording-complete" in response.text


def test_recording_complete_webhook_returns_goodbye(monkeypatch):
    use_config(monkeypatch, make_config())
    client = TestClient(main.app)

    response = client.post("/api/telephony/recording-complete", data={"CallSid": "CA1"})

    assert response.status_code == 200
    assert "<Hangup" in response.text


# --- Recording status callback ---------------------------------------------


def test_recording_callback_schedules_processing(monkeypatch):
    use_config(monkeypatch, make_config())
    seen: dict[str, Any] = {}

    async def fake_process(**kwargs: Any) -> None:
        seen.update(kwargs)

    monkeypatch.setattr(main, "process_voicemail_recording_safe", fake_process)
    client = TestClient(main.app)

    response = client.post(
        "/api/telephony/recording",
        data={
            "RecordingUrl": "https://api.twilio.com/.../Recordings/RE9",
            "RecordingSid": "RE9",
            "CallSid": "CA9",
            "From": "+14155550123",
        },
    )

    assert response.status_code == 204
    assert seen["recording_url"] == "https://api.twilio.com/.../Recordings/RE9"
    assert seen["recording_sid"] == "RE9"
    assert seen["call_sid"] == "CA9"
    assert seen["from_number"] == "+14155550123"
    assert seen["config"].provider == "twilio"


def test_signalwire_recording_callback_schedules_processing(monkeypatch):
    use_config(
        monkeypatch,
        make_config(
            provider="signalwire",
            account_sid="project_test",
            auth_token="api_token_test",
            signing_key="signing_key_test",
        ),
    )
    seen: dict[str, Any] = {}

    async def fake_process(**kwargs: Any) -> None:
        seen.update(kwargs)

    monkeypatch.setattr(main, "process_voicemail_recording_safe", fake_process)
    client = TestClient(main.app)

    response = client.post(
        "/api/telephony/recording",
        data={
            "RecordingUrl": "https://space.signalwire.com/api/laml/.../Recordings/RE9",
            "RecordingSid": "RE9",
            "CallSid": "CA9",
            "From": "+14155550123",
            "RecordingStatus": "completed",
        },
    )

    assert response.status_code == 204
    assert seen["recording_url"] == "https://space.signalwire.com/api/laml/.../Recordings/RE9"
    assert seen["recording_sid"] == "RE9"
    assert seen["call_sid"] == "CA9"
    assert seen["from_number"] == "+14155550123"
    assert seen["config"].provider == "signalwire"


def test_recording_callback_without_url_is_noop(monkeypatch):
    use_config(monkeypatch, make_config())
    called = False

    async def fake_process(**kwargs: Any) -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(main, "process_voicemail_recording_safe", fake_process)
    client = TestClient(main.app)

    response = client.post("/api/telephony/recording", data={"CallSid": "CA9"})

    assert response.status_code == 204
    assert called is False


def test_recording_callback_rejects_bad_signature(monkeypatch):
    use_config(monkeypatch, make_config(validate_signature=True, auth_token="real_token"))
    client = TestClient(main.app)

    response = client.post(
        "/api/telephony/recording",
        data={"RecordingUrl": "https://api.twilio.com/.../Recordings/RE9"},
        headers={"X-Twilio-Signature": "not-a-valid-signature"},
    )

    assert response.status_code == 403


def test_signalwire_signature_header_is_used(monkeypatch):
    use_config(
        monkeypatch,
        make_config(
            provider="signalwire",
            account_sid="project_test",
            auth_token="api_token_test",
            signing_key="signing_key_test",
            validate_signature=True,
        ),
    )

    def fake_request_is_authentic(*, url, params, signature, config):
        assert signature == "signalwire-signature"
        assert config.provider == "signalwire"
        return False

    monkeypatch.setattr(main, "request_is_authentic", fake_request_is_authentic)
    client = TestClient(main.app)

    response = client.post(
        "/api/telephony/voice",
        data={"CallSid": "signalwire-call"},
        headers={"X-SignalWire-Signature": "signalwire-signature"},
    )

    assert response.status_code == 403


# --- End-to-end processing pipeline (mocked I/O) ---------------------------


def test_process_voicemail_runs_stt_then_intake(monkeypatch, tmp_path):
    from telephony import service

    monkeypatch.setenv("VOICEMAIL_OUTPUT_DIR", str(tmp_path))

    async def fake_download(recording_url, config, **kwargs):
        assert recording_url == "https://api.twilio.com/.../Recordings/RE5"
        return b"audio-bytes", "audio/wav", "RE5.wav"

    async def fake_transcribe(audio_bytes, filename, content_type=None):
        assert audio_bytes == b"audio-bytes"
        return TranscriptionResponse(id="tr_RE5", transcript="Hi, this is Maria.")

    def fake_run_intake(stt_json):
        assert stt_json["transcript"] == "Hi, this is Maria."
        return {"first_name": "Maria", "request": {"type": "refill"}}

    monkeypatch.setattr(service, "download_recording", fake_download)
    monkeypatch.setattr(service, "transcribe_audio", fake_transcribe)
    monkeypatch.setattr(service, "_run_intake", fake_run_intake)

    record = asyncio.run(
        service.process_voicemail_recording(
            recording_url="https://api.twilio.com/.../Recordings/RE5",
            recording_sid="RE5",
            call_sid="CA5",
            from_number="+14155550123",
            config=make_config(),
        )
    )

    assert record["intake"]["first_name"] == "Maria"
    assert record["transcript"] == "Hi, this is Maria."
    assert record["from_number"] == "+14155550123"
    assert record["telephony_provider"] == "twilio"

    intake_file = tmp_path / "RE5.intake.json"
    stt_file = tmp_path / "RE5.stt.json"
    assert json.loads(intake_file.read_text())["first_name"] == "Maria"
    assert json.loads(stt_file.read_text())["transcript"] == "Hi, this is Maria."


def test_process_voicemail_with_no_transcript_skips_intake(monkeypatch, tmp_path):
    from telephony import service

    monkeypatch.setenv("VOICEMAIL_OUTPUT_DIR", str(tmp_path))

    async def fake_download(recording_url, config, **kwargs):
        return b"silent-audio-bytes", "audio/wav", "RE0.wav"

    async def fake_transcribe(audio_bytes, filename, content_type=None):
        return TranscriptionResponse(id="tr_RE0", transcript="")

    def fail_run_intake(stt_json):
        raise AssertionError("Intake should not run without a transcript")

    monkeypatch.setattr(service, "download_recording", fake_download)
    monkeypatch.setattr(service, "transcribe_audio", fake_transcribe)
    monkeypatch.setattr(service, "_run_intake", fail_run_intake)

    record = asyncio.run(
        service.process_voicemail_recording(
            recording_url="https://api.twilio.com/.../Recordings/RE0",
            recording_sid="RE0",
            call_sid="CA0",
            from_number="+14155550123",
            config=make_config(),
        )
    )

    assert record["status"] == "intake_skipped_no_transcript"
    assert record["transcript"] == ""
    assert record["telephony_provider"] == "twilio"
    assert record["intake"] == {
        "status": "skipped",
        "reason": "no_transcript",
        "message": "Recording did not contain a usable speech transcript.",
    }

    intake_file = tmp_path / "RE0.intake.json"
    voicemail_file = tmp_path / "RE0.voicemail.json"
    assert json.loads(intake_file.read_text())["reason"] == "no_transcript"
    assert json.loads(voicemail_file.read_text())["status"] == "intake_skipped_no_transcript"
