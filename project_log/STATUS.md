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

## In progress
- Idea/scope still being finalized (project name, SMS sponsor, calendar provider for the Scheduling action agent, whether triage agent stays in scope).
- Next.js app integration is not wired to the STT or schedule-eligibility services yet.
- Schedule eligibility agent has not been run against the live Supabase project yet — needs `SUPABASE_URL`/`SUPABASE_SERVICE_ROLE_KEY`/`ANTHROPIC_API_KEY` filled into `backend/api/.env`.

## Blockers
- SMS sponsor TBD.
- Calendar integration choice TBD for the Scheduling action agent (Google Calendar vs. internal-only, per latest notes leaning internal).
- Deepgram API key must be added locally as `DEEPGRAM_API_KEY` before live transcription calls work.

## Next
- Wire `backend/api/.env` with real Supabase + Anthropic credentials and run `scheduling_eligibility.cli` against the seeded Robert Martinez conflict scenario from `docs/database/README.md`.
- Build the Prescription Requirement Eligibility Agent next (same pattern: deterministic checks + Claude summary).
- Build the Eligibility Agent (insurance acceptance / missing-info checklist).
- Decide whether the future Next.js app will proxy FastAPI or port the API contracts into TypeScript routes.
- Pick sponsor/tool for confirmation (SMS).
