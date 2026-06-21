# CHW Dashboard — Handoff

_Last updated: 2026-06-21_

The **CHW approval dashboard** (`dashboard/`): a certified health worker reviews voicemail-derived
tasks and approves / rejects / handles them in one place. It consumes the orchestrator's eligibility
output from the Supabase `tasks` table. (Separate from `berkapp/`, the EHR mock.)

---

## TL;DR — where we are

- ✅ **Dashboard is fully built** (queue + history), live-wired to Supabase, themed to match berkapp. Builds clean.
- ✅ **Approve actually executes** locally: refill/reschedule call the real FastAPI executors → write `prescriptions`/`appointments` + send a patient confirmation SMS.
- ✅ **Orchestrator routing verified** end-to-end (all 10 demo scenarios route to the right path).
- ⏳ **Decided next step: "Option B"** — move *all* DB access into the FastAPI backend so the dashboard holds no Supabase key. **Most of the backend endpoints this needs are NOT built yet** (see [Backend gap](#backend-coverage-gap)).
- ⏳ **Backend is not deployed** (only the two Vercel frontends are). Deploying it is now a prerequisite.

---

## Architecture & data flow

```
voicemail → Deepgram STT → intake extraction → ORCHESTRATOR (eligibility gates)
        → writes a row to Supabase `tasks`
              (task_type, status, agent_summary, agent_checks, proposed_action, flagged_reason)
        → DASHBOARD reads `tasks` (+ joins patients & voicemails) → CHW decision
        → EXECUTOR (FastAPI) writes prescriptions/appointments/messages + confirmation SMS
        → reflects back in berkapp (chart / encounters inbox)
```

The orchestrator **produces**; the dashboard **consumes** — decoupled through the `tasks` table.
Our `Task` type mirrors the DB columns 1:1 so there's no translation layer.

---

## Data model (the contract)

`Task` (see `dashboard/lib/types.ts`) — field names match the DB columns exactly:

| field | notes |
|---|---|
| `id`, `patient_id`, `voicemail_id` | |
| `patient_name` | **joined** from `patients` (no column on `tasks`) |
| `task_type` | `prescription_refill` \| `reschedule` \| `message_relay` \| `escalate` |
| `status` | `pending_approval` \| `escalated` \| `rejected` \| `complete` |
| `agent_summary`, `agent_checks` (nested JSON), `proposed_action` (JSON), `flagged_reason` | from the orchestrator |
| `approved_at`, `approved_by` | pre-existing audit columns |
| `chw_note`, `reviewed_at`, `rejected_at` | **added by migration `0001`** (see below) |
| `transcript` | joined from `voicemails`; `patient_dob`/`patient_phone` joined from `patients` |

**Buckets** (derived, `lib/task.ts`): `to_review` (pending_approval/escalated) · `follow_up` (rejected) · `done` (complete).
**Actionable** = the 3 non-`escalate` types. **Iffy** = actionable + `escalated` (gate failed; CHW can still approve/reject with a note).

---

## What's built & working

**Dashboard (`dashboard/`):** Next.js 16 / React 19 / Tailwind v4 / Geist.
- `/` — work queue: urgency-ordered **To review** + **Rejected (follow-up)** + **Done**. Two-click review → Approve/Reject; non-actionable → "Action taken"; rejected → "Mark done".
- `/history` — Excel-style filterable/sortable log of all past decisions.
- Optimistic decision writes with revert-on-error + Undo. Fixtures fallback + "Demo data" banner when the DB is unreachable.
- Theme matched to berkapp (slate + sky + teal header).

**Backend executors that exist (`backend/api/`):**
- `POST /api/prescriptions` → inserts a `prescriptions` row, marks task `complete`, sends confirmation SMS.
- `POST /api/appointments` → books the appointment, marks task `complete`, sends confirmation SMS.

**Verified:**
- Orchestrator routes all 10 demo intakes correctly (clean → `pending_approval` w/ executable action; every failure → `escalated` w/ a specific reason; emergency → safety bypass).
- Live reads work; the live `tasks` rows match the orchestrator's output.
- A real Approve through the dashboard inserted a prescription + flipped status + reported the confirmation result.
- Reject + note persists to the DB (read back directly from Supabase).

---

## Where the dashboard touches the DB right now

All server-side, service-role key, funneled through **two files**:
- `lib/supabase.ts` — the `supabaseAdmin()` client (the only connection).
- `lib/tasks-repo.ts` — all queries: `getTasks()`, `getTask()`, `getPatientIdentity()` (reads) and **`patchTask()` (the only write)**.

Callers: `app/page.tsx`, `app/history/page.tsx`, `app/api/tasks/route.ts` (reads); `app/api/tasks/[id]/route.ts` (the decision PATCH → `patchTask`); `lib/executor.ts` (calls the FastAPI executors for approve).

> ⚠️ The dashboard currently holds the **service-role key** (bypasses RLS). Option B removes it.

---

## Decided plan — "Option B": backend owns all DB access

**End state:** the FastAPI backend owns every read and write; the dashboard talks only to the backend over HTTP (no Supabase client, no key).

### New backend endpoints to build
1. **`GET /api/tasks`** — enriched task list. Port of the dashboard's `getTasks()`/`mapRow()` join logic into Python; must emit the `Task` shape above (already snake_case).
2. **`PATCH /api/tasks/{id}/decision`** — body `{decision, note?, status?, chw?}`. Absorbs the dashboard's `patchFor()` + `patchTask()` + `executor.ts`. Handles:
   - `approve` → dispatch on `proposed_action.type`: refill→`fill_prescription`, reschedule→`book_appointment`, relay→**new relay executor (a)**, escalate-stub→status-only; then write audit fields + confirmation SMS.
   - `reject` → `status=rejected` + audit, then **auto denial SMS (b)** with a manual-follow-up notice if it fails.
   - `action_taken` / `mark_done` / `reopen` → status writes (+ clear audit on reopen).
   - **Idempotency (c):** no-op if already `complete`.
   - Returns `{task, notice}` (re-read + mapped), same shape the UI already consumes.

### Dashboard side (after the endpoints exist)
- `app/page.tsx` + `app/history/page.tsx` → `fetch(${BACKEND_API_URL}/api/tasks)` server-side.
- `app/api/tasks/[id]/route.ts` → thin **proxy** to the backend decision endpoint (browser still calls same-origin `/api/tasks/[id]`, so client code is unchanged; no CORS).
- **Delete** `lib/supabase.ts`, `lib/tasks-repo.ts`, `lib/executor.ts`; remove `@supabase/supabase-js` + `SUPABASE_*` keys. `lib/task.ts` presenters stay.

### Sequencing (no broken intermediate state)
1. Backend `GET /api/tasks` — curl-verify shape. 2. Backend `PATCH …/decision` (+ a/b/c). 3. Point dashboard at backend; full local test. 4. Delete dashboard DB layer + key. 5. Update env examples / README.

---

## Backend coverage gap

What Option B needs vs. what exists today:

| Scenario | Built? | Today lives in |
|---|---|---|
| `GET /api/tasks` (enriched read) | ❌ | dashboard `getTasks()` |
| Approve → refill / reschedule | ✅ | `/api/prescriptions`, `/api/appointments` |
| Approve → **message relay** (insert `messages`) — **(a)** | ❌ | nothing (`/api/message-relay` is only the classifier, not delivery) |
| **Reject** + denial SMS — **(b)** | ❌ | dashboard `patchTask`; `send_denial_notice()` exists but has no endpoint |
| `action_taken` / `mark_done` / `reopen` | ❌ | dashboard `patchTask` |
| Audit writes (`approved_by`/`chw_note`/`reviewed_at`/`rejected_at`) | ❌ | dashboard (executors only write `{status, approved_at}`) |
| **Idempotency** guard — **(c)** | ❌ | nothing (caused duplicate `prescriptions` rows in testing) |

**2 of ~8 scenarios built.** Most missing ones are trivial ports of the dashboard's `patchFor()` logic (~30 lines). Non-trivial: `GET /api/tasks` (join port), (a) relay executor (insert one `messages` row → shows up in berkapp encounters), (b) denial SMS endpoint, (c) idempotency check.

---

## The `messages` table (for relay executor / piece a)

Already exists and is **live** (berkapp's encounters page reads it — not hardcoded):
`id, task_id, patient_id, provider_id, message_body, delivered, created_at`.
The relay executor just inserts a row (`message_body` = draft, `delivered=true`) + marks the task complete → it appears in the doctor's inbox in berkapp automatically. Handle the `provider_id == null` case (patient with no preferred provider).

---

## Run it locally

**Backend (FastAPI):**
```bash
cd backend/api
./.venv/bin/pip install -r requirements.txt        # first time
./.venv/bin/uvicorn main:app --port 8000
```
Needs `backend/api/.env` (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, DEEPGRAM_API_KEY, ANTHROPIC_API_KEY).
**`TEXTBELT_API_KEY` is missing → confirmation/denial SMS won't actually send** (returns a reason; pipeline still works).

**Dashboard:**
```bash
cd dashboard
npm install
npm run dev                                         # http://localhost:3000
```
`dashboard/.env.local` needs: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `BACKEND_API_URL=http://localhost:8000`.
(After Option B, the dashboard will need only `BACKEND_API_URL`.)

**Orchestrator routing check (offline, no DB/paid APIs):**
```bash
cd backend
PYTHONPATH="$(pwd):$(pwd)/orchestrator:$(pwd)/api" api/.venv/bin/python -m orchestrator.main_loop --pretty
```

---

## Database migration (ALREADY RUN ✅)

`dashboard/db/migrations/0001_chw_decision_columns.sql` added `chw_note`, `reviewed_at`, `rejected_at`
to `tasks`. Run once via **Supabase dashboard → SQL Editor**. Idempotent. (DDL can't be run via the
service key, only in the SQL editor.) Already applied to the live project.

---

## Deployment status

| Piece | Where | Status |
|---|---|---|
| `berkapp` (EHR) | Vercel | live: `berkapp-three.vercel.app` |
| `dashboard` (ours) | Vercel | live: `dashboard-azure-six-79.vercel.app` |
| `backend/api` (FastAPI) | Procfile (`uvicorn main:app --port $PORT`) | **NOT deployed** — needs Railway/Render |

**To deploy for real:**
1. Deploy `backend/api` → get a public URL.
2. Set `BACKEND_API_URL` on Vercel (dashboard project) → that URL. Set `SUPABASE_*` + `TEXTBELT_API_KEY` + `ANTHROPIC_API_KEY` etc. on the backend host.
3. **After Option B, the deployed dashboard hard-depends on the deployed backend** (reads go through it too). Until the backend is deployed, the dashboard falls back to fixtures.

---

## Open items / decisions

- **Build the Option B backend endpoints** (`GET /api/tasks`, `PATCH /api/tasks/{id}/decision`) + pieces **(a) relay executor, (b) reject denial SMS, (c) idempotency**. This is the prerequisite for the whole migration. (These touch `backend/api/` — coordinate so we don't collide.)
- **Multi-request voicemails**: a single voicemail asking for two things (e.g. refill + relay) currently yields only **one** task. Orchestrator limitation — flag to its owners.
- **Set `TEXTBELT_API_KEY`** on the backend so confirmation/denial SMS actually send.
- **Duplicate prescriptions** exist in the demo DB from idempotency-less test approves — clean up once (c) lands.
- Keep the **fixtures fallback** (demo data when backend is down)? Recommended: yes.

---

## Key files

```
dashboard/
  app/page.tsx, app/history/page.tsx        # server pages (read tasks)
  app/api/tasks/route.ts                    # GET tasks
  app/api/tasks/[id]/route.ts               # PATCH decision (approve/reject/action_taken/mark_done/reopen)
  lib/supabase.ts                           # service-role client      ⟵ DELETE in Option B
  lib/tasks-repo.ts                         # getTasks/getTask/patchTask (DB)  ⟵ MOVE to backend
  lib/executor.ts                           # calls FastAPI executors  ⟵ MOVE into decision endpoint
  lib/types.ts, lib/task.ts, lib/status.ts  # Task shape + derivations/presenters (stay)
  components/                               # AppShell, DashboardClient, TaskSection, TaskRow, HistoryTable, ...
  db/migrations/0001_chw_decision_columns.sql

backend/api/
  main.py                                   # routes (executors live here)
  prescription_fulfillment/, scheduler/     # the two built executors
  confirmation/                             # send_confirmation + send_denial_notice (SMS)
backend/orchestrator/
  main_loop.py                              # demo routing harness; canonical task shape
```
