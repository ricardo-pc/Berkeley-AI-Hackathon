from __future__ import annotations

from twilio.twiml.voice_response import VoiceResponse

DEFAULT_GREETING = (
    "Thank you for calling the clinic. No one is available to take your call right now. "
    "After the beep, please leave a message with your first and last name, your full date of birth, your phone number, your insurance plan, "
    "and the reason for your call. Press the pound key when you are finished."
)

GOODBYE_MESSAGE = "Thank you. Your message has been received. Goodbye."

NO_RECORDING_MESSAGE = "We did not receive a recording. Goodbye."


def build_voicemail_twiml(
    *,
    action_url: str,
    recording_status_callback_url: str,
    greeting: str | None = None,
    max_length_seconds: int = 120,
) -> str:
    """TwiML for the voicemail box: greet the caller, then record their message.

    ``action_url`` controls the in-call flow once recording stops (so the call
    ends gracefully instead of looping back to this same webhook).
    ``recording_status_callback_url`` is hit asynchronously by Twilio once the
    recording file is ready to download, which is where we run STT + intake.
    """
    response = VoiceResponse()
    response.say(greeting or DEFAULT_GREETING, voice="Polly.Joanna")
    response.record(
        action=action_url,
        method="POST",
        max_length=max_length_seconds,
        play_beep=True,
        finish_on_key="#",
        trim="trim-silence",
        recording_status_callback=recording_status_callback_url,
        recording_status_callback_method="POST",
        recording_status_callback_event="completed",
    )
    # Reached only if the caller never recorded anything (e.g. immediate hang-up
    # paths handled by Twilio); keeps the flow from dead-ending silently.
    response.say(NO_RECORDING_MESSAGE, voice="Polly.Joanna")
    response.hangup()
    return str(response)


def build_goodbye_twiml() -> str:
    """TwiML returned to the ``<Record action>`` callback to end the call."""
    response = VoiceResponse()
    response.say(GOODBYE_MESSAGE, voice="Polly.Joanna")
    response.hangup()
    return str(response)
