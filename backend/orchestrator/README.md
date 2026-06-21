# Orchestrator Service

Deployable service for intake-facing eligibility orchestration. It exposes:

- `GET /health`
- `POST /api/refill`
- `POST /api/reschedule`
- `POST /api/message-relay`

Each `POST` accepts the intake extraction payload from the intake service plus
optional `task_id`.

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
