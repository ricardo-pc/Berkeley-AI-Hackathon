# Orchestrator Service

Deployable service for intake-facing eligibility orchestration. It exposes:

- `GET /health`
- `POST /api/refill`
- `POST /api/reschedule`
- `POST /api/message-relay`

Each `POST` accepts the intake extraction payload from the intake service plus
optional `task_id`.

## Output

This service **takes no action of its own**. It only produces an eligibility
decision and, when eligible, the *plan* for what should happen. Every endpoint
resolves to exactly one of two modes:

1. **Pass eligibility** (`status: pending_approval`) — the request is approvable.
   The plan is written to the `tasks` table as `proposed_action` and waits there.
   The execution **engine** carries it out only once a human clicks **Approve**.
2. **Escalate** (`status: escalated`, or `rejected` for message relay) — the
   request cannot be auto-approved. `proposed_action` is `null` and a human has to
   handle the request manually. `flagged_reason` explains why.

Response fields:

- `status` — the mode above.
- `flagged_reason` — human-readable reason when escalated, else `null`.
- `checks` / `agent_checks` — the full reasoning trail (surfaced in the dashboard).
- **`proposed_action`** — the queued plan. Present only on the pass path; `null`
  on escalate. Nothing runs at response time — it is the engine's input later.

When `task_id` is supplied, the service writes `status`, `agent_summary`,
`agent_checks`, `proposed_action`, and `flagged_reason` onto that `tasks` row.
That row **is** the queue entry the engine reads at approve time.

### `proposed_action` shapes (the task the executor consumes)

`POST /api/refill` → `prescription_eligibility/service.py`:

```json
{
  "type": "prescription_refill",
  "medication_name": "Lisinopril",
  "dosage": "10mg",
  "instructions": "once daily",
  "provider_id": "<from the matching prior prescription, may be null>",
  "patient_id": "<uuid>"
}
```

`POST /api/reschedule` → `scheduling_eligibility/service.py` (uses the requested
slot when free, otherwise the next available slot it found):

```json
{
  "type": "reschedule",
  "cancel_appointment_id": "<uuid or null>",
  "new_start": "2026-06-24T09:00:00+00:00",
  "new_end": "2026-06-24T09:30:00+00:00",
  "provider_id": "<uuid>"
}
```

`POST /api/message-relay` → `message_relay/service.py`:

```json
{
  "type": "message_relay",
  "assignee": "physician",
  "patient_id": "<uuid>",
  "provider_id": "<uuid or null>",
  "message": "<drafted relay message>"
}
```

Escalation path (e.g. insurance not accepted in `main.py`) emits a non-executable
action that keeps the task in the flagged queue:

```json
{ "type": "escalate", "reason": "insurance plan not accepted" }
```

### What the engine does with `proposed_action.type` on Approve

The orchestrator performs none of these writes. When a human clicks **Approve**,
the downstream engine reads the queued `tasks.proposed_action` and performs exactly
one write:

| `proposed_action.type` | Write the engine performs |
|---|---|
| `prescription_refill` | INSERT a new row into `prescriptions` |
| `reschedule` | UPDATE the existing `appointments` row to `rescheduled` + INSERT a new row at the proposed slot |
| `message_relay` | UPDATE `messages.delivered = true` |
| `escalate` | No write — stays in the flagged queue for manual CHW action |

See `docs/database/README.md` §7 (Approval Flow) for the canonical mapping.

The offline demo loop still runs demo intake JSON files through:

- intake output evaluation
- patient resolution
- insurance eligibility
- request-specific eligibility for prescription refills, reschedules, and message relay

The loop is offline by default and uses the seeded demo fixtures from `docs/database/README.md`.

```bash
python3 -m backend.orchestrator.main_loop --pretty
```

To save the task-style JSON payloads:

```bash
python3 -m backend.orchestrator.main_loop \
  --input-dir demo/intake_output \
  --output demo/orchestrator_results.json \
  --pretty
```

## Heroku

Deploy this directory to the `heroku-eligibility` remote:

```bash
git subtree push --prefix backend/orchestrator heroku-eligibility main
```

Required config vars:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `ANTHROPIC_API_KEY`
