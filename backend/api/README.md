# API

Backend service tying agents together and serving the dashboard.

## Speech-to-text slice

This folder currently exposes the portable Deepgram transcription layer. The code is intentionally split so FastAPI and the CLI both call the same framework-independent service.

### Setup

```bash
cd backend/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill in `DEEPGRAM_API_KEY` in `.env`, or export it in your shell.
Fill in `ANTHROPIC_API_KEY` to run intake extraction.

### CLI usage

```bash
cd backend/api
python3 -m transcription.cli ../../demo/voicemails/sample.wav --pretty
python3 -m transcription.cli ../../demo/voicemails/sample.wav --pretty --output result.json
```

### API usage

```bash
cd backend/api
uvicorn main:app --reload --port 8000
```

```bash
curl -X POST \
  -F "file=@../../demo/voicemails/sample.wav" \
  http://localhost:8000/api/transcriptions
```

The API and CLI return the same JSON contract as `contracts/transcription_response.example.json`.

### Compact and intake API usage

```bash
curl -X POST \
  -F "file=@../../demo/james.wav" \
  http://localhost:8000/api/transcriptions/text
```

```bash
curl -X POST \
  -F "file=@../../demo/james.wav" \
  http://localhost:8000/api/voicemail/intake
```

```bash
curl -X POST http://localhost:8000/api/intake \
  -H "Content-Type: application/json" \
  -d '{"stt_json":{"transcript":"Hi, this is Maria Gonzalez. I need a refill for Lisinopril 10 milligrams once daily with food."}}'
```

`/api/intake` and `/api/voicemail/intake` return sanitized intake output: structured patient fields, request content detection, preferred-time objects, missing fields, and compact transcript text.

## Schedule Adjustment Eligibility Service

`../orchestrator/scheduling_eligibility/` checks whether a reschedule request can proceed:

- Calendar conflicts — clinic holidays, provider working hours, and overlapping booked appointments (reads `providers` + `appointments` from Supabase, schema in [docs/database](../../docs/database/README.md)).
- Repeated-request abuse — flags a patient for a manual call once they've made more than 2 consecutive reschedule requests since their last completed visit.

The conflict/consecutive-request logic is pure Python (`checks.py`, fully unit tested). `service.py` orchestrates the checks against a `ScheduleEligibilityRepo` (Supabase-backed in `repo.py`, fake-able in tests) and returns deterministic structured `checks`; task write-back maps those checks into the legacy `tasks.agent_checks` column and clears `tasks.agent_summary`.

### Setup

Same venv as above, plus:

```bash
cd backend/orchestrator
pip install -r requirements.txt
```

Fill in `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` in `.env`.

### CLI usage

```bash
cd backend/orchestrator
python3 -m scheduling_eligibility.cli \
  --patient-id <uuid> --provider-id <uuid> \
  --start 2026-06-25T09:00:00+00:00 --end 2026-06-25T09:30:00+00:00 \
  --pretty
```

### API usage

Workflow endpoints now accept intake-shaped payloads so request routing comes from `intake.request.type`.

```bash
curl -X POST http://localhost:8000/api/schedule-eligibility \
  -H "Content-Type: application/json" \
  -d '{"intake":{"first_name":"Robert","last_name":"Martinez","date_of_birth":"1952-01-30","phone_number":"415-555-0174","insurance_plan":"United Healthcare","request":{"type":"reschedule","details":"Move appointment to June 24th at 3 PM","orders":[],"preferred_times":[{"raw_text":"June 24th at 3 PM","date":"2026-06-24","start_time":"15:00","time_of_day":"afternoon"}],"urgency_signal":"routine"},"requests":[],"missing_fields":[],"transcript":"This is Robert Martinez. I need to move my appointment to June 24th at 3 PM."},"provider_id":"b1b2c3d4-0001-0001-0001-000000000001","requested_start":"2026-06-24T15:00:00+00:00","requested_end":"2026-06-24T15:30:00+00:00"}'
```
