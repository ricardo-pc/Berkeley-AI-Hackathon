# Status

Last updated: 2026-06-21

See [docs/PROJECT_PLAN.md](../docs/PROJECT_PLAN.md) for the full agent-by-agent breakdown and test cases. This file is the quick "what's actually true right now" snapshot.

## Done — backend agents (all in `backend/api/`, all with regression tests)
- **Eligibility agents**: `scheduling_eligibility`, `prescription_eligibility`, `message_relay` — each does deterministic checks + a Claude (Haiku) summary, writes back into the `tasks` row by `task_id` (merging into `agent_checks` rather than overwriting it, so multiple agents touching the same task don't clobber each other).
- **Action agents**: `scheduler` (books/reschedules appointments) and `prescription_fulfillment` (writes the refill) — both now also mark the `tasks` row `status=complete` + `approved_at` when given a `task_id`, closing the loop from eligibility → execution → done. Verified live: booked Robert Martinez's pre-approved slot through the real scheduler and confirmed it shows up as completed.
- **Confirmation Agent** (`confirmation/`) — sends an SMS via **Textbelt** (switched from Twilio: trial accounts can't register for A2P 10DLC, so Twilio sends were silently carrier-filtered). Only fires for `prescription_refill`/`reschedule`, never `message_relay`. Verified live, twice, with real delivery confirmed. Message template now matches the agreed wording (pharmacy name for refills, doctor's name for reschedules).
- **Summary Agent** (`summary/`) — read-only digest over `tasks`: completed/flagged/pending buckets by status, missing-insurance read directly from `patients.insurance_valid` (not `agent_checks`, since not every agent path writes that key). Optional Claude narrative on top. Verified live against Supabase.
- **Triage fix**: the emergency-keyword check used to only run inside the message-relay branch of `orchestrator/main_loop.py` — a refill/reschedule call mentioning chest pain would never trigger it. Moved to a global pre-check at the top of `run_intake()`, before patient resolution or task-type dispatch. Caught a real previously-untested fixture (`08_emergency_symptoms_escalation`) that was escalating for the wrong, vague reason ("request type unknown") instead of being flagged urgent.
- Decided **not** to build Triage Sentinel as its own agent — the fix above covers the actual gap.
- Orchestrator (`orchestrator/`) runs all demo intake fixtures end-to-end offline, covering all 6 documented test-case scenarios plus edge cases.
- 117 tests passing (`python -m pytest tests/`).

## Done — frontend (Jay/Robert's side, not this thread's work, noted for context)
- EHR replica + `FrictionMeter` (counts clicks/seconds — a deliberate "before" demo prop, not the real product) (`berkapp/`).
- `/schedule` calendar page — provider columns, 15-min grid, live Supabase data.
- Patient-scoped Rx page; login screen removed (site goes straight to `/ehr`).

## Known gaps (flagged, not yet acted on)
- **No task-approval dashboard exists anywhere** — the literal headline feature (voicemail tasks → one-click approve) isn't built. Explicitly deprioritized for now in favor of backend polish; revisit before the demo.
- **Orchestrator duplicates logic instead of calling the real packages** for prescription/message-relay (only reschedule reuses the real `scheduling_eligibility` package). Two parallel implementations of the same checks — a demo-strategy decision (which one is "the real pipeline"), not pulled the trigger on yet.
- **Eligibility Agent (insurance + intake-completeness gate) isn't a standalone package** — lives inline in `orchestrator/main_loop.py`.
- **Textbelt key issue unresolved**: balance went 50→47 after 3 successful sends, then reported `quotaRemaining: -1` (undocumented value) on the 4th attempt and every check since. Emailed `support@textbelt.com` with the key + purchase details; Textbelt has a 30-day money-back guarantee if it doesn't get sorted. A second key was deliberately *not* purchased yet pending their reply, to avoid repeating whatever caused this.

## Next
- Hear back from Textbelt support; decide refund vs. retry.
- Decide who/when builds the task-approval dashboard.
- Decide the orchestrator-vs-real-agents reconciliation.
