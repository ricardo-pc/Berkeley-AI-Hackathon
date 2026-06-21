# Berkeley-AI-Hackathon

Project name: TBD

Cuts down unnecessary time on simple, repetitive tasks at a hospital front desk. Missed voicemails (prescription refills, schedule adjustments, message relays) pile up and are slow to triage by hand. This project turns voicemails into a dashboard where a certified healthcare worker (CHW) can approve repetitive tasks with one click, while edge cases are surfaced for manual review.

## Live Deployments

- `berkapp` EHR demo: https://berkapp-three.vercel.app
- `dashboard` CHW approval dashboard: https://dashboard-azure-six-79.vercel.app

## Structure

- `agents/` — pipeline agents, one subfolder each:
  - `intake/` — extracts patient name, reason, preferred times, insurance, urgency from a voicemail
  - `eligibility/` — checks insurance acceptance, flags missing info
  - `prescription/` — checks refill eligibility (visit history, dosage match, conflicting meds)
  - `scheduling/` — finds an appointment slot given provider availability and urgency
  - `confirmation/` — generates outbound SMS/email/call-script confirmations
  - `triage/` — flags calls needing human escalation (may be cut from scope)
  - `summary/` — daily digest for the front desk
- `dashboard/` — CHW-facing UI for approving tasks and reviewing edge cases
- `backend/api/` — service layer tying agents to the dashboard
- `backend/db/` — patient/visit/prescription/scheduling records
- `demo/voicemails/` — uploaded audio files standing in for real inbound calls
- `docs/` — hackathon guide, architecture notes, work division
- `scripts/` — setup/dev/demo utilities
- `tests/` — regression tests (per mentor guidance)

Hackathon guide: https://docs.google.com/document/d/1jDaXilfjTSa9BbqRuAdPdshSbloZhGSzVslIkJORmc4/edit?usp=sharing
