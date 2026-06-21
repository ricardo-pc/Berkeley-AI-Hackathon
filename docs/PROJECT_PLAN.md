# Project Plan

Project Name: TBD

## Value proposition

Cut down unnecessary time on simple tasks that can be automated. Tens/hundreds of missed calls pile up by the end of the day at a hospital — time-consuming to listen to every call, write down important material, and execute the patient's request. Especially since the majority of missed calls are one of three things: prescription refill requests, schedule adjustments, or a request to relay a message to the doctor (e.g. "I don't feel well"). Executing each of these requires a series of clicking and reading that takes longer than the action itself.

## Product goal

Go through every voicemail and collect it into a dashboard where one approval click from a certified healthcare worker (CHW) executes the repetitive task, and edge cases get organized for the CHW to read and act on. Unfinished and finished tasks live in the same dashboard.

## Mentor notes

- Regression testing — every agent below ships with tests pinned to specific scenarios, not just happy-path checks.

## Architecture overview

```
Voicemail
   │
   ▼
Intake Agent ──────────► extracts patient, request type, details
   │
   ▼
Triage Sentinel ───────► emergency keywords? → escalate immediately, skip everything below
   │ (no)
   ▼
Eligibility Agent ─────► insurance accepted + intake fields complete? → if not, escalate
   │ (OK)
   ▼
   ├─ prescription_refill → Prescription Requirement Eligibility Agent
   ├─ reschedule          → Schedule Adjustment Eligibility Agent
   └─ message_relay       → Message Relay Eligibility Agent
   │
   ▼ (eligible)
Scheduling Agent (action) → writes the actual appointment row once a slot is pre-approved
   │
   ▼ (CHW clicks Approve)
Backend executes proposed_action → writes prescriptions/appointments/messages
   │
   ▼
Confirmation Agent ────► sends SMS/email
   │
   ▼
Summary Agent ─────────► daily digest
```

Every agent reads and writes the same shared `tasks` row in Supabase (identified by `task_id`) — there's no direct agent-to-agent messaging. See [docs/database/README.md](database/README.md) for the full schema.

## Agents

### Intake Agent — ✅ built (`agents/intake/`)

Receives a Deepgram/STT JSON transcript (or text input for the demo) and extracts, with Claude:

- First and last name, date of birth, phone number, insurance plan
- A `requests` array (a single voicemail can contain more than one workflow item, e.g. a refill *and* a message relay) — each entry has `type`, `details`, `orders`, `preferred_times`, `urgency_signal`
- `preferred_times` are resolved to structured `{raw_text, date, start_time, time_of_day}` objects with relative dates ("next Tuesday") already converted to absolute dates — not left as raw text for a downstream agent to re-parse
- `missing_fields` for whatever the caller didn't provide

Sponsor: Deepgram (speech-to-text).

> Note: an earlier sketch of this agent's output showed each field with a confidence score (`{"value": ..., "confidence": 0.98}`). The actual implementation returns plain values without per-field confidence — worth knowing if anyone is building against the original sketch instead of `agents/intake/schemas.py`.

CLI: `python3 -m agents.intake.cli path/to/stt-output.json --pretty`

### Eligibility Agent — partially built (folded into the orchestrator, not a standalone package)

Two checks, both gating everything downstream:

1. **Intake completeness** — does the extraction have first/last name, DOB, phone, and request details? Missing fields → escalate with a "what we need" checklist instead of guessing.
2. **Insurance accepted** — is the patient's plan on file and valid? Invalid insurance short-circuits straight to escalated *before* any type-specific agent runs (no point checking calendar conflicts for a patient who can't be seen here).

Inbound calls that don't qualify (missing required fields) go to manual review by the maintainer, or — proposed, not built — a Poke SMS follow-up asking the caller for the missing details.

This logic currently lives inline in `orchestrator/main_loop.py` rather than as its own agent package; pulling it into a standalone `agents/eligibility` module (mirroring the pattern the other agents use) is still open.

### Prescription Requirement Eligibility Agent — ✅ built (`backend/api/prescription_eligibility/`)

Checks whether a patient meets the requirements for a refill — answers "can this go through automatically, or does a human need to look at it first?" Four checks against the real database:

1. **Recent visit** — seen within the required window. The window isn't fixed: under 65 needs a visit in the last 6 months, 65+ gets 12 months (mirrors real per-doctor policy where established chronic patients get more leeway).
2. **Upcoming visit** — is one already scheduled within the next year? No upcoming visit means no follow-up plan even if recently seen.
3. **Identical dosage match** — same medication, same dosage and instructions as before. A first-time prescription or a dosage change can't be auto-refilled.
4. **Drug interaction warning** — is the patient on another medication known to conflict with this one? This is a *warning, not a blocker* — mirrors the MyChart/eClinicalWorks popup; it doesn't stop an otherwise-eligible refill, it flags it for the physician to notice.

**Expected output**
- Eligible (3 of 3 hard requirements pass): `eligible: true`, `status: "pending_approval"`, a `proposed_action` with exactly what to write on approval. A drug conflict still shows up in `agent_checks` (`conflict: true`, `conflict_medication`) without changing the outcome.
- Ineligible (any hard requirement fails): `eligible: false`, `status: "escalated"`, `proposed_action: null`, `flagged_reason` spelling out exactly which requirement(s) failed.

**Test cases**
- Pure logic: age-based window selection, a visit just inside vs. far outside the window, identical vs. changed dosage, never-prescribed-before, known conflict pair flagged vs. unrelated medication not flagged.
- Service tests against the real seeded patients: Maria Gonzalez (eligible, Lisinopril/Amlodipine interaction surfaces as a warning), James Okafor (escalated — last visit 19 months ago, nothing upcoming), never-prescribed-before, missing patient raises a clear error.
- Write-back tests: passing `task_id` writes into that `tasks` row and *merges* with whatever another agent already wrote there instead of erasing it; omitting `task_id` touches nothing.

### Schedule Adjustment Eligibility Agent — ✅ built and tested live (`backend/api/scheduling_eligibility/`)

Checks whether a patient meets the requirements to adjust their schedule:

1. **Calendar conflicts** — another patient already booked in the preferred time, doctor availability, holiday/non-work days.
2. **Repeated-request pattern** — has the patient been continuously asking for a schedule change? (Sometimes done to "renew" prescription-refill eligibility without ever showing up.) More than 2 consecutive requests → escalate for a manual call to confirm the real reason.

**Expected output** — one of three outcomes:
1. **Clear to proceed** — `eligible: true`, `status: "pending_approval"`, `suggested_timeslot` confirming the requested time is bookable, `proposed_action` ready for the CHW to approve, a Claude-generated plain-English summary.
2. **Needs a different time** — slot taken / outside hours / holiday. `eligible: false`, but `status` stays `"pending_approval"` (not escalated — it's a routine fix). `suggested_timeslot` and `proposed_action` are both empty; finding the alternate time is the Scheduling Agent's job, not this one's.
3. **Needs a phone call** — 3+ consecutive reschedules. `eligible: false`, `status: "escalated"`, `flagged_reason` explains why.

Writes back into the same `tasks` row identified by `task_id` (status, agent_summary, agent_checks, proposed_action, flagged_reason) — merged with whatever's already there, not overwritten.

**Tested live against Supabase** with the Robert Martinez seeded conflict scenario — correctly detected the conflict and (once a free slot was supplied manually) correctly proposed it.

### Message Relay Eligibility Agent — ✅ built (`backend/api/message_relay/`)

Filters out requests that don't fall into one of: a negative status update, an unreasonable reaction to medication, any discomfort, or a request for some form of accommodation.

Returns whether it's worth relaying, the patient's first/last name and DOB, and a concise draft message to relay to the doctor. Also resolves the patient's `preferred_provider_id` to know who to route to, and flags (without blocking) a mismatch if the voicemail names a different doctor than the one on file.

### Scheduling Agent (action) — ✅ built (`backend/api/scheduler/`)

Receives an identity and a *pre-approved* time slot, and writes it to the calendar. Validation already happened upstream (the eligibility step) — this agent just resolves the patient, marks the old appointment "rescheduled" if one is being moved, and inserts the new appointment row.

Input:
```json
{
  "patient_id": "...", "first_name": "Robert", "last_name": "Martinez", "dob": "1952-01-30",
  "provider_id": "b1b2c3d4-0001-0001-0001-000000000001",
  "start_time": "2026-06-25T09:00:00", "end_time": "2026-06-25T09:30:00",
  "cancel_appointment_id": "c1b2c3d4-0004-0004-0004-000000000004",
  "visit_type": "follow_up"
}
```
(`cancel_appointment_id` and `visit_type` are optional; omit `cancel_appointment_id` for a brand-new booking instead of a reschedule.)

Output:
```json
{
  "success": true,
  "message": "Booked Robert Martinez with provider ... from ... to ...",
  "patient": { "id": "...", "first_name": "Robert", "last_name": "Martinez", "dob": "1952-01-30" },
  "rescheduled_from": "c1b2c3d4-0004-...",
  "appointment": { "id": "...", "provider_id": "...", "start_time": "...", "end_time": "...", "visit_type": "follow_up", "status": "scheduled" }
}
```

### Confirmation Agent — ❌ not built (`agents/confirmation/`)

Generates an outbound call script or SMS/email confirmation with all details, follow-up instructions, and what to bring. SMS sponsor still TBD.

### Triage Sentinel — ❌ not built, may be cut (`agents/triage/`)

Flags calls that need human escalation: chest pain, suicidal ideation, active bleeding — anything that should bypass the automation pipeline entirely. The orchestrator's message-relay path currently does a lightweight version of this (keyword check for emergency phrases before deciding to relay a message), but there's no standalone agent.

### Summary Agent — ❌ not built (`agents/summary/`)

Produces a structured daily digest for the front desk: who was scheduled, what was flagged, what's still pending, what insurance info is missing.

### Orchestrator — ✅ built (`orchestrator/`)

Runs the demo intake JSON files end-to-end (intake validation → patient resolution → insurance check → type-specific eligibility) and is the thing that currently proves the pipeline works, scenario by scenario. It's offline-only, against in-memory demo fixtures (`orchestrator/demo_fixtures.py`) — it reuses the real, tested `scheduling_eligibility` package for reschedules, but has its own simplified inline logic for prescription refills and message relay rather than calling the live `prescription_eligibility`/`message_relay` packages against Supabase. Worth reconciling before the demo so there's one source of truth instead of two parallel implementations of the same checks.

```bash
python3 -m orchestrator.main_loop --pretty
```

## Test cases (also covered by `tests/test_orchestrator_main_loop.py`)

1. **Maria Gonzalez — fully automated, gets the SMS.** Lisinopril refill, insurance valid, all three hard requirements pass → `eligible: true`, `pending_approval`. Also flags a drug interaction with her active Amlodipine — a note, not a blocker. CHW approves → backend inserts the new `prescriptions` row → (once built) Confirmation Agent texts her. Proves a *warning* and an *escalation* aren't the same thing.
2. **James Okafor — escalated, never reaches a human-approval click.** Metformin refill, last visit 19 months ago, nothing upcoming → `eligible: false`, `escalated`, `flagged_reason` spells out why. No `proposed_action`, so nothing to one-click approve.
3. **Linda Chen — escalated before the type-specific agent even runs.** Kaiser Permanente isn't accepted → short-circuits to `escalated` before the Schedule Adjustment Eligibility Agent is even called. Shows why agent *order* matters.
4. **Robert Martinez — neither escalated nor approved, stuck in between.** Wants a slot that's already booked → `eligible: false`, `pending_approval` (not escalated) — needs a different slot, not a phone call. The Scheduling Agent (once wired into the live pipeline rather than just the orchestrator) picks this up and proposes the next open slot.
5. **(Hypothetical) Someone who's rescheduled 3 times in a row.** Same agent, `requires_manual_call: true` this time → `escalated`, but for a different reason than Linda or James. Three patients can all land in "escalated" — the dashboard needs to surface `flagged_reason`, not just the status badge.
6. **Priya Sharma vs. a "just calling to say hi" voicemail.** Priya's dizziness/nausea after starting Sertraline is an adverse reaction — worth relaying. A voicemail with no actionable content should get filtered out silently by the Message Relay Eligibility Agent rather than ever reaching a human.

## Tech architecture

No live phone number for the demo — audio files get uploaded as "voicemails" instead. (A live Twilio number was explored as a flashy bonus add-on; parked for now — see [project_log/STATUS.md](../project_log/STATUS.md) if revisiting.)

## Work division

- **Robert** — Web UI for voice transcription.
- **Ricardo** — Database with mock patient data, testing agent↔database connections, the Scheduling Agent.

## Resources

- Hackathon guide: see root [README.md](../README.md).
