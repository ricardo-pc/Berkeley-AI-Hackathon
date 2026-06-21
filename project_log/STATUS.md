# Status

Last updated: 2026-06-21

See [docs/PROJECT_PLAN.md](../docs/PROJECT_PLAN.md) for the full agent-by-agent breakdown and test cases. This file is the quick "what's actually true right now" snapshot.

## Architecture, post-restructuring

Two backend services now, not one:

- **`backend/api/`** — transcription, intake extraction, live telephony (SignalWire/Twilio: call → voicemail → STT → intake), the two action agents (`scheduler`, `prescription_fulfillment`), `confirmation` (Textbelt SMS), `summary`. The eligibility-check routes (`/api/schedule-eligibility`, `/api/prescription-eligibility`) are now thin proxies that forward to `backend/orchestrator`.
- **`backend/orchestrator/`** — a separately deployable service: `scheduling_eligibility`, `prescription_eligibility`, `message_relay`, plus the insurance/intake-completeness gate (`_insurance_escalation`) and patient resolution (via `patients.preferred_provider_id`, defaulting the provider automatically). This used to be the root-level offline `orchestrator/` demo runner; it's now real and Supabase-backed.

These are two separate Python services (separate `requirements.txt`/`Procfile`/`.env`) — code isn't shared between them by import; small pieces (like the denial-notice logic) are intentionally duplicated rather than cross-imported, since a shared package name across both sys.path roots would collide in the test suite.

## Done — backend
- **Eligibility agents** (`backend/orchestrator/{scheduling,prescription}_eligibility`): deterministic checks, write back into `tasks` by `task_id` (merging into `agent_checks`, never overwriting). Claude/Haiku summary calls were dropped from both (intentional simplification) — `agent_summary` is written as `None`.
- **Scheduling Agent now actually finds alternative slots** (`scheduling_eligibility/checks.py::find_next_available_slot`) — previously only the offline demo had this; now the real Supabase-backed agent does. Searches forward from the requested time, reuses the already-fetched appointments list, respects holidays/hours/exclusions. If nothing opens within 14 days, escalates instead of leaving `proposed_action` null. Verified live against real conflicting appointments.
- **Action agents** (`backend/api/{scheduler,prescription_fulfillment}`): book/refill, then mark the `tasks` row `status=complete` + `approved_at` when given a `task_id` — closes the loop from eligibility → execution → done. Verified live.
- **Confirmation Agent** (`backend/api/confirmation`): sends SMS via **Textbelt** (switched from Twilio — trial accounts can't register for A2P 10DLC, sends were silently carrier-filtered). Fires for `prescription_refill`/`reschedule` only, never `message_relay`. Message wording: pharmacy name for refills, doctor's name for reschedules.
- **Denial notices**: symmetric counterpart, sent when an eligibility check escalates a refill/reschedule (`"Please call us back"`, deliberately generic — never leaks specific clinical/insurance reasons over SMS). Lives in `backend/orchestrator/main.py` (inlined, not a shared package — see architecture note above) since that's where the eligibility decision actually happens now. Verified live against James Okafor's real escalated refill (correctly attempted, failed only on the still-unresolved Textbelt quota issue, degraded gracefully).
- **Summary Agent** (`backend/api/summary`): read-only digest over `tasks`. Missing-insurance read directly from `patients.insurance_valid`, not `agent_checks` (not every agent path writes that key).
- **Triage fix**: emergency-keyword check moved from message-relay-only to a global pre-check at the top of intake handling — a refill/reschedule call mentioning chest pain now correctly bypasses automation instead of slipping through.
- **Live telephony** (`backend/api/telephony`): real call → voicemail → STT → intake pipeline, using SignalWire/Twilio. (The team picked this up independently after we'd parked it as a demo bonus — now actually built.)
- 154 tests passing (`python -m pytest tests/`).

## Done — frontend
- **`dashboard/`** — a new, separate Next.js app: the actual task-approval dashboard (`DashboardClient`, `TaskRow`, `StatusTabs`, `DigestStrip`). Currently on mock data (`lib/mockData.ts`). This was the literal headline-feature gap flagged earlier tonight — now in progress.
- **`berkapp/`** — the EHR replica + `FrictionMeter` ("before" demo prop), `/schedule` calendar, `/encounters` view. This is the "old, painful way" demo, not the new product.

## Known gaps
- **`dashboard/` is still on mock data** — not wired to real Supabase `tasks` yet.
- **Two backend services, not unified under one deploy** — fine for now, but worth knowing if demo day needs both running simultaneously (different ports/processes).
- **Textbelt key issue unresolved**: balance went 50→47 after 3 successful sends, then `quotaRemaining: -1` (undocumented) on every check since. Emailed support with key + purchase details; 30-day money-back guarantee exists if unresolved. Deliberately not buying a second key yet, pending their reply.
- **Orchestrator's Claude usage**: dropped from scheduling/prescription eligibility (intentional, by Robert). `message_relay`'s classifier and `summary`'s narrative still call Claude, so the project still uses it meaningfully elsewhere — worth knowing if anyone's tracking the Claude-sponsor angle specifically.

## Next
- Wire `dashboard/` to real Supabase data instead of mocks.
- Hear back from Textbelt support; decide refund vs. retry.
- Confirm both backend services actually run together cleanly for the live demo.
