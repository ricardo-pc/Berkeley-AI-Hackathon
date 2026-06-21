# CHW Dashboard — Handoff

_Last updated: 2026-06-21_

The **CHW approval dashboard** (`dashboard/`): a certified health worker reviews voicemail-derived
tasks and approves / rejects / handles them in one place. It consumes the orchestrator's eligibility
output (the Supabase `tasks` table) **via the FastAPI backend** — the dashboard itself has no DB access.
(Separate from `berkapp/`, the EHR mock.)

---

## TL;DR — where we are

- ✅ **Dashboard fully built** (queue + history), themed to match berkapp. Builds clean (tsc/lint/build).
- ✅ **Option B done:** the FastAPI backend owns **all** DB reads/writes + the **single decision executor**. The dashboard talks only to the backend over HTTP and holds **no Supabase key**.
- ✅ **Approve executes for real** (locally): refill/reschedule write `prescriptions`/`appointments`, relay writes `messages` (→ shows in berkapp encounters), all send patient SMS (when `TEXTBELT_API_KEY` is set).
- ✅ **Reject auto-texts the patient** a denial notice, with a manual-follow-up fallback if it can't send.
- ✅ **Idempotent** (re-approving a `complete` task no-ops) + a **Reset button** restores the demo baseline.
- ✅ **Orchestrator routing verified** (all demo scenarios route to the right path).
- ⏳ **Not deployed yet:** the FastAPI backend has no public URL. Deploying it + setting `BACKEND_API_URL` on Vercel is the remaining step (see [Deployment](#deployment)).

---

## Architecture & data flow

```
voicemail → Deepgram STT → intake extraction → ORCHESTRATOR (eligibility gates)
        → writes a row to Supabase `tasks`
              (task_type, status, agent_summary, agent_checks, proposed_action, flagged_reason)
        → FastAPI backend  GET /api/tasks         (reads + joins patients/voicemails)
        → DASHBOARD renders the queue → CHW decision
        → FastAPI backend  PATCH /api/tasks/{id}/decision   (the ONE executor)
              approve → prescriptions / appointments / messages + confirmation SMS
              reject  → status=rejected + denial SMS
        → reflects back in berkapp (chart / encounters inbox)
```

**The dashboard makes zero direct DB calls.** Everything goes through the backend, which is the only
holder of the Supabase service-role key. The orchestrator **produces** tasks; the dashboard **consumes**
them through the backend — decoupled via the `tasks` table.

---

## Data model (the contract)

`Task` (`dashboard/lib/types.ts`) — field names match the DB columns 1:1:

| field | notes |
|---|---|
| `id`, `patient_id`, `voicemail_id` | |
| `patient_name` | **joined** from `patients` (no column on `tasks`) |
| `task_type` | `prescription_refill` \| `reschedule` \| `message_relay` \| `escalate` |
| `status` | `pending_approval` \| `escalated` \| `rejected` \| `complete` |
| `agent_summary`, `agent_checks` (nested JSON), `proposed_action` (JSON), `flagged_reason` | from the orchestrator |
| `approved_at`, `approved_by` | pre-existing audit columns |
| `chw_note`, `reviewed_at`, `rejected_at` | **added by migration `0001` (already run)** |
| `transcript` (from `voicemails`), `patient_dob`/`patient_phone` (from `patients`) | joined |

**Buckets** (derived, `lib/task.ts`): `to_review` (pending_approval/escalated) · `follow_up` (rejected) · `done` (complete).
**Actionable** = the 3 non-`escalate` types. **Iffy** = actionable + `escalated` (gate failed; CHW can still approve/reject with a note).

---

## Backend — the single surface the dashboard talks to (`backend/api/tasks/`)

| Endpoint | Purpose |
|---|---|
| `GET /api/tasks` | Enriched task list (joins patients + voicemails) → exact `Task` shape. |
| `PATCH /api/tasks/{id}/decision` | **The one executor.** Body `{decision, note?, status?, chw?}`. |
| `POST /api/demo/baseline` | Snapshot current demo state (tasks + side-effect row ids). |
| `POST /api/demo/reset` | Restore to the saved baseline; deletes prescription/appointment/message rows created since. |

`PATCH …/decision` dispatches internally (plain function calls, reusing the existing services):
- **approve** → `prescription_refill`→`fill_prescription`, `reschedule`→`book_appointment`, `message_relay`→insert `messages`, escalate/iffy-override→status-only; then writes audit fields + chains the confirmation SMS. **Idempotent** (no-op if already `complete`).
- **reject** → `status=rejected` + audit, then auto denial SMS with a manual-follow-up notice if it fails.
- **action_taken / mark_done / reopen** → status writes (`reopen` clears audit; used by Undo).

Files: `tasks/repo.py` (Supabase access), `tasks/service.py` (executor + row→Task mapping), `tasks/demo.py` (baseline/reset), `tasks/router.py` (FastAPI routes). Registered via one line in `backend/api/main.py`. The older `POST /api/prescriptions` + `/api/appointments` still exist (untouched); the decision endpoint reuses their service functions.

---

## Dashboard side (Option B cutover)

- `lib/backend.ts` — **the only** server-side data access: `fetchTasks()`, `postDecision()`, `resetDemo()` (reads `BACKEND_API_URL`).
- `app/page.tsx` / `app/history/page.tsx` → `fetchTasks()`. Fixtures fallback + "Demo data" banner when the backend is unreachable.
- `app/api/tasks/route.ts`, `app/api/tasks/[id]/route.ts`, `app/api/demo/reset/route.ts` → **thin proxies** to the backend (browser still calls same-origin routes → no CORS).
- `components/ResetDemoButton.tsx` — in the queue header; POST `/api/demo/reset` → `router.refresh()`.
- `lib/useLiveTasks.ts` — polls `/api/tasks` so the queue auto-refreshes.
- **Deleted:** `lib/supabase.ts`, `lib/tasks-repo.ts`, `lib/executor.ts`. **Removed** `@supabase/supabase-js`. The dashboard env needs only `BACKEND_API_URL`.

---

## Run it locally

**1. Backend (FastAPI) — must be running first:**
```bash
cd backend/api
./.venv/bin/pip install -r requirements.txt        # first time
./.venv/bin/uvicorn main:app --port 8000
```
Needs `backend/api/.env`: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `DEEPGRAM_API_KEY`, `ANTHROPIC_API_KEY`,
and **`TEXTBELT_API_KEY`** (without it, confirmation/denial SMS won't actually send — returns a reason; pipeline still works).

**2. Dashboard:**
```bash
cd dashboard
npm install
npm run dev                                         # http://localhost:3000
```
`dashboard/.env.local` needs only: `BACKEND_API_URL=http://localhost:8000`.

**Demo reset:** click "Reset demo" in the queue header (or `POST /api/demo/reset`). To change the baseline,
get the demo into the desired state then `POST /api/demo/baseline`. Current baseline: 4 pending + 2 escalated.

**Orchestrator routing check (offline, no DB/paid APIs):**
```bash
cd backend
PYTHONPATH="$(pwd):$(pwd)/orchestrator:$(pwd)/api" api/.venv/bin/python -m orchestrator.main_loop --pretty
```

---

## Deployment

| Piece | How | Status | What it needs |
|---|---|---|---|
| `berkapp` (EHR) | Vercel | ✅ live: `berkapp-three.vercel.app` | `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` |
| `dashboard` (this) | Vercel | ✅ live: `dashboard-azure-six-79.vercel.app` | **`BACKEND_API_URL`** (now its only required env) |
| `backend/api` (FastAPI) | Procfile (`uvicorn main:app --port $PORT`) | ❌ **NOT deployed** | `SUPABASE_*`, `TEXTBELT_API_KEY`, `ANTHROPIC_API_KEY`, `DEEPGRAM_API_KEY` |

### What can be deployed right now
- **berkapp + dashboard** are already deployable on Vercel and are live.
- **backend/api is deploy-ready** (has a Procfile; runs cleanly locally) but **isn't hosted yet** — it just needs a host (Railway / Render / Fly) and its env vars.

### Steps to a fully working live demo
1. **Deploy `backend/api`** to Railway/Render → get a public URL (e.g. `https://clinic-api.up.railway.app`). Set its env: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `ANTHROPIC_API_KEY`, `DEEPGRAM_API_KEY`, `TEXTBELT_API_KEY`.
2. **Set `BACKEND_API_URL`** on the Vercel **dashboard** project → that URL. Redeploy.
3. Done — server-to-server (Vercel → FastAPI), so no CORS to configure.

### ⚠️ Hard dependency
Since Option B, the **deployed dashboard depends on the deployed backend** for *all* data (reads too).
If `BACKEND_API_URL` is unset/unreachable, the dashboard renders the fixtures (with the "Demo data" banner)
rather than live tasks. So **the backend must be deployed for the live dashboard to show real data.**

---

## Open items

- **Set `TEXTBELT_API_KEY`** on the backend so confirmation/denial SMS actually send (currently they no-op with a reason).
- **Deploy `backend/api`** + set `BACKEND_API_URL` in Vercel (above).
- **Stray task:** there are two "Maria Gonzalez" refills in the demo data (`f1b2c3d4-0001…` + `5dd6b103-aac6…`) — likely a leftover test task; confirm/remove for a clean demo.
- **Multi-request voicemails:** a single voicemail asking for two things (e.g. refill + relay) currently yields only **one** task — orchestrator limitation, flag to its owners.

---

## Key files

```
dashboard/
  app/page.tsx, app/history/page.tsx        # server pages → fetchTasks()
  app/api/tasks/route.ts                    # GET proxy
  app/api/tasks/[id]/route.ts               # PATCH decision proxy
  app/api/demo/reset/route.ts               # reset proxy
  lib/backend.ts                            # the only data access (→ BACKEND_API_URL)
  lib/types.ts, lib/task.ts, lib/status.ts  # Task shape + derivations/presenters
  lib/useLiveTasks.ts                        # polling hook
  components/                               # AppShell, Sidebar, DashboardClient, TaskSection,
                                            #   TaskRow, HistoryTable, ResetDemoButton, Toast, ...
  db/migrations/0001_chw_decision_columns.sql   # (already run)

backend/api/
  tasks/                                    # repo.py, service.py (executor+mapper), demo.py, router.py
  main.py                                   # registers tasks.router; legacy executor endpoints
  prescription_fulfillment/, scheduler/     # the two executors the decision endpoint reuses
  confirmation/                             # send_confirmation + send_denial_notice (SMS)
backend/orchestrator/
  main_loop.py                              # demo routing harness; canonical task shape
```
