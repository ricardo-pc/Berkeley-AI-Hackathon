# Status

Last updated: 2026-06-20

## Done
- Repo initialized, idea drafted (README.md).
- Preemptive folder structure created: agents/*, dashboard/, backend/{api,db}, demo/voicemails, docs, scripts, tests, project_log.
- Deepgram speech-to-text layer implemented in `backend/api`:
  - FastAPI `GET /health` and `POST /api/transcriptions`.
  - Reusable transcription package used by both API and CLI.
  - CLI supports local audio files via `python -m transcription.cli <audio-file> --pretty`.
  - Stable JSON contract fixture added for future Next.js portability.
  - Regression tests added for API contract, CLI contract, Deepgram parsing, missing API key, provider failure, route name, and upload field.

## In progress
- Idea/scope still being finalized (project name, SMS sponsor, calendar provider, whether triage agent stays in scope).
- Next.js app integration is not wired to the STT service yet.

## Blockers
- SMS sponsor TBD.
- Calendar integration choice TBD (Google Calendar?).
- DB choice TBD.
- Deepgram API key must be added locally as `DEEPGRAM_API_KEY` before live transcription calls work.

## Next
- Run the CLI against demo voicemail audio once `DEEPGRAM_API_KEY` is configured.
- Decide whether the future Next.js app will proxy FastAPI or port the `/api/transcriptions` contract into a TypeScript route.
- Pick sponsor/tool for confirmation (SMS).
- Decide on calendar integration.
- Start on intake agent after transcript output is validated.
