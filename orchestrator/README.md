# Orchestrator

Runs the demo intake JSON files through:

- intake output evaluation
- patient resolution
- insurance eligibility
- request-specific eligibility for prescription refills, reschedules, and message relay

The loop is offline by default and uses the seeded demo fixtures from `docs/database/README.md`.
It reuses the tested schedule eligibility service in `backend/api/scheduling_eligibility`.

```bash
python3 -m orchestrator.main_loop --pretty
```

To save the task-style JSON payloads:

```bash
python3 -m orchestrator.main_loop \
  --input-dir demo/intake_output \
  --output demo/orchestrator_results.json \
  --pretty
```

