# Status

Last updated: 2026-06-20

See [docs/PROJECT_PLAN.md](../docs/PROJECT_PLAN.md) for the full agent-by-agent breakdown and test cases. This file is the quick "what's actually true right now" snapshot.

## Done
- Database schema + seed data live in Supabase (`docs/database/README.md`), including `patients.preferred_provider_id`.
- Deepgram speech-to-text: FastAPI service (`backend/api/transcription/`) and ported into the Next.js app (`berkapp/app/api/transcriptions/route.ts`).
- Intake Agent (`agents/intake/`): Claude extraction from STT JSON, resolves relative dates into structured `preferred_times` (`{raw_text, date, start_time, time_of_day}`), supports multiple requests per voicemail via a `requests` array. Still in progress on the team's side — parked for now from this end.
- Schedule Adjustment Eligibility Agent (`backend/api/scheduling_eligibility/`) — tested live against Supabase (Robert Martinez conflict scenario).
- Prescription Requirement Eligibility Agent (`backend/api/prescription_eligibility/`) — tested live against Supabase (Maria Gonzalez eligible-with-warning, James Okafor escalated scenarios).
- Message Relay Eligibility Agent (`backend/api/message_relay/`) — classifies whether a message is worth relaying, resolves the patient's preferred provider, flags doctor-name mismatches.
- Scheduling Agent / action agent (`backend/api/scheduler/`) — writes a pre-approved slot to the calendar (marks old appointment rescheduled, inserts the new one). Wired into `main.py` as `POST /api/appointments`.
- **Prescription Fulfillment Agent / action agent (`backend/api/prescription_fulfillment/`) — the previously-missing refill executor.** Mirrors the Scheduling Agent: resolves the patient, inserts the new `prescriptions` row. Wired as `POST /api/prescriptions`. Tested live against Supabase (Maria Gonzalez).
- **Confirmation Agent (`backend/api/confirmation/`)** — sends an SMS via Twilio, but only for prescription refills and reschedules, never message relay. Chained automatically after both action agents above; a failed send is best-effort and never undoes the booking/refill.
- Orchestrator (`orchestrator/`) — runs the demo intake fixtures end-to-end offline (intake validation → patient resolution → insurance gate → type-specific eligibility), covering all 6 documented test-case scenarios plus a few extra edge cases (unknown patient, missing fields, dosage mismatch).
- All agents that write to `tasks.agent_checks` merge into the existing JSONB instead of overwriting it, so multiple agents touching the same task don't clobber each other.
- Frontend: patient list + per-patient EHR pages wired to Supabase (`berkapp/app/api/patients/`, `berkapp/app/_lib/ehr.ts`).
- Fixed: orchestrator crashed on the new structured `preferred_times` shape (3 failing tests) — now reads `date`/`start_time` directly instead of assuming plain strings.
- 89 tests passing across the whole suite (`python -m pytest tests/`).

## In progress / gaps
- **Twilio not configured yet.** `TWILIO_ACCOUNT_SID`/`TWILIO_AUTH_TOKEN`/`TWILIO_FROM_NUMBER` need to go into `backend/api/.env` before any confirmation text can actually send — the agent is built and unit-tested, but not yet live-fired.
- **Eligibility Agent (insurance + intake completeness gate) isn't a standalone package** — that logic currently lives inline in `orchestrator/main_loop.py`. Should probably get pulled into its own agent module to match the pattern of the others.
- **Orchestrator duplicates logic instead of calling the real packages.** It reuses the tested `scheduling_eligibility` package for reschedules, but has its own simplified inline prescription/message-relay logic against in-memory fixtures rather than calling `prescription_eligibility`/`message_relay` against live Supabase. Two parallel implementations of the same checks — worth reconciling before the demo.
- Triage Sentinel and Summary Agent are still README stubs — decided not to build Triage Sentinel as its own agent (fold the existing emergency-keyword check, currently only inside the orchestrator's message-relay branch, into a global pre-check instead); Summary Agent is next up (pure read-only query over `tasks`, no eligibility-style logic needed).
- Live phone number (Twilio inbound) explored as a flashy demo bonus, parked for now in favor of the upload-based demo path. (Twilio is now in use for *outbound* confirmations regardless.)

## Blockers
- Twilio account/number not yet provisioned — confirmations are built but can't fire until that's done.
- Live phone number demo intentionally parked, not blocking.

## Next
- Provision Twilio, add credentials to `.env`, smoke-test a real confirmation send.
- Build the Summary Agent (digest over `tasks`, no LLM strictly required).
- Move the emergency-keyword check out of the orchestrator's message-relay branch into a global pre-check that runs on every voicemail.
- Reconcile the orchestrator's offline logic with the real DB-backed agents, or decide the orchestrator is the source of truth for the demo and the DB-backed packages are the "real" implementation for later.
- Pull insurance/intake-completeness eligibility out of the orchestrator into its own `agents/eligibility` package.
