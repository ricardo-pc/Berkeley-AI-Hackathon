# Eligibility Service

Standalone FastAPI service for refill and schedule eligibility checks.

## Endpoints

- `GET /health`
- `POST /api/prescription-eligibility`
- `POST /api/schedule-eligibility`

Both endpoints read from Supabase through the service role key. When `task_id`
is provided, they write deterministic `checks` into the existing
`tasks.agent_checks` column and clear `tasks.agent_summary`.

## Local Run

```bash
cd backend/eligibility_service
pip install -r requirements.txt
uvicorn main:app --reload
```

## Heroku

Deploy this directory as the Heroku app root. Required environment variables:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
