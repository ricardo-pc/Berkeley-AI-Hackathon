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

## Schedule Adjustment Eligibility Agent

`scheduling_eligibility/` checks whether a reschedule request can proceed:

- Calendar conflicts — clinic holidays, provider working hours, and overlapping booked appointments (reads `providers` + `appointments` from Supabase, schema in [docs/database](../../docs/database/README.md)).
- Repeated-request abuse — flags a patient for a manual call once they've made more than 2 consecutive reschedule requests since their last completed visit.

The conflict/consecutive-request logic is pure Python (`checks.py`, fully unit tested). `service.py` orchestrates the checks against a `ScheduleEligibilityRepo` (Supabase-backed in `repo.py`, fake-able in tests) and calls Claude (`claude_summary.py`, Anthropic API) only to write the plain-English `agent_summary` shown to the CHW.

### Setup

Same venv as above, plus:

```bash
cd backend/api
pip install -r requirements.txt
```

Fill in `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, and `ANTHROPIC_API_KEY` in `.env`.

### CLI usage

```bash
cd backend/api
python3 -m scheduling_eligibility.cli \
  --patient-id <uuid> --provider-id <uuid> \
  --start 2026-06-25T09:00:00+00:00 --end 2026-06-25T09:30:00+00:00 \
  --pretty
```

### API usage

```bash
curl -X POST http://localhost:8000/api/schedule-eligibility \
  -H "Content-Type: application/json" \
  -d '{"patient_id":"<uuid>","provider_id":"<uuid>","requested_start":"2026-06-25T09:00:00+00:00","requested_end":"2026-06-25T09:30:00+00:00"}'
```
