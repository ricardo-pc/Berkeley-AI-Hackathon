# Intake Agent

Receives Deepgram/STT JSON and extracts strict intake fields with Claude:

- first name
- last name
- date of birth
- phone number
- insurance plan
- nested request details:
  - type
  - details
  - orders
  - preferred times
  - urgency signal
- `requests` array for voicemails that contain more than one workflow item, such as a refill plus a doctor-message relay

The field names line up with the database reference in `docs/database/README.md`: `first_name`, `last_name`, `date_of_birth`, `phone_number`, and `insurance_plan` map to patient identity/contact information; `request.type` and `transcript` map to the voicemail request.

## CLI

Run from the repo root with a saved Deepgram/normalized STT JSON file:

```bash
python3 -m agents.intake.cli path/to/stt-output.json --pretty
```

Requires `ANTHROPIC_API_KEY` in the shell or in an `.env` file.
