# Status

Last updated: 2026-06-20

## Done
- Repo initialized, idea drafted (README.md).
- Preemptive folder structure created: agents/*, dashboard/, backend/{api,db}, demo/voicemails, docs, scripts, tests, project_log.
- Database schema reference written: `docs/database/README.md` (7 tables, SQL, seed data, agent-to-table map, Supabase config, approval flow). Supabase project provisioned from this schema.
- Deepgram speech-to-text layer implemented in `backend/api`:
  - FastAPI `GET /health` and `POST /api/transcriptions`.
  - Reusable transcription package used by both API and CLI.
  - CLI supports local audio files via `python -m transcription.cli <audio-file> --pretty`.
  - Stable JSON contract fixture added for future Next.js portability.
  - Regression tests added for API contract, CLI contract, Deepgram parsing, missing API key, provider failure, route name, and upload field.
- Schedule Adjustment Eligibility Agent implemented in `backend/api/scheduling_eligibility`:
  - FastAPI `POST /api/schedule-eligibility`, CLI `python -m scheduling_eligibility.cli`.
  - Deterministic checks (`checks.py`): clinic holidays, provider working hours, overlapping booked appointments, and a manual-call flag once a patient has made more than 2 consecutive reschedule requests since their last completed visit.
  - Supabase-backed repo (`repo.py`) behind a `ScheduleEligibilityRepo` protocol so the service is testable without hitting the real DB.
  - Claude (Anthropic API) used only to generate the plain-English `agent_summary` for the CHW (`claude_summary.py`) — Claude sponsor track.
  - 14 regression tests added (calendar conflict, consecutive-reschedule threshold, service orchestration, missing provider, missing Supabase config, missing Anthropic key, Claude response parsing).
- Deepgram speech-to-text API ported into the Next.js app at `berkapp/app/api/transcriptions/route.ts`.
- Intake Agent implemented in `agents/intake`:
  - Reads Deepgram/normalized STT JSON and extracts patient/request fields with Claude.
  - Request-related fields live under nested `request` with `type`, `details`, `orders`, `preferred_times`, and `urgency_signal`.
  - CLI `python3 -m agents.intake.cli <stt-json-file> --pretty`.
  - Tests cover transcript parsing, strict Claude JSON extraction, missing Anthropic key, invalid Claude JSON, service orchestration, and CLI output.

## In progress
- Idea/scope still being finalized (project name, SMS sponsor, calendar provider for the Scheduling action agent, whether triage agent stays in scope).
- Frontend upload/recording UI is not created yet.
- Next.js app integration is not wired to the schedule-eligibility service yet.
- Schedule eligibility agent has not been run against the live Supabase project yet — needs `SUPABASE_URL`/`SUPABASE_SERVICE_ROLE_KEY`/`ANTHROPIC_API_KEY` filled into `backend/api/.env`.
- Intake agent has not been run against the live Anthropic API yet — needs `ANTHROPIC_API_KEY` configured.

## Blockers
- SMS sponsor TBD.
- Calendar integration choice TBD for the Scheduling action agent (Google Calendar vs. internal-only, per latest notes leaning internal).
- Deepgram API key must be added locally as `DEEPGRAM_API_KEY` before live transcription calls work.

## Next
- Wire `backend/api/.env` with real Supabase + Anthropic credentials and run `scheduling_eligibility.cli` against the seeded Robert Martinez conflict scenario from `docs/database/README.md`.
- Build the Prescription Requirement Eligibility Agent next (same pattern: deterministic checks + Claude summary).
- Build the Eligibility Agent (insurance acceptance / missing-info checklist).
- Run the CLI against demo voicemail audio once `DEEPGRAM_API_KEY` is configured.
- Build a frontend upload/recording UI that calls Next.js `POST /api/transcriptions`.
- Feed saved STT JSON into `agents.intake.cli` once a real demo transcription is generated.
- Pick sponsor/tool for confirmation (SMS).
