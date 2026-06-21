-- CHW decision/audit columns for the approval dashboard.
-- Run once in the Supabase SQL editor (Project → SQL Editor → New query).
--
-- The tasks table already has approved_at + approved_by (used for completions).
-- These add the reject pathway + audit note the CHW workflow needs.
-- `status` is free-text, so no constraint change is needed for 'rejected'.

alter table public.tasks
  add column if not exists chw_note    text,
  add column if not exists reviewed_at timestamptz,
  add column if not exists rejected_at timestamptz;

-- Optional: speed up the dashboard's status-bucketed reads.
create index if not exists tasks_status_created_idx
  on public.tasks (status, created_at desc);
