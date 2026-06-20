# Schedule Adjustment Eligibility Agent

Checks whether a patient meets the requirements to adjust their schedule (separate from the [Scheduling Agent](../scheduling/README.md), which finds the actual slot once a request is approved):

- Calendar conflicts: another patient already booked in the preferred time, doctor availability, holiday/non-work days.
- Repeated-request abuse: if a patient has made more than 2 consecutive reschedule requests since their last completed visit, flag for a manual call to confirm the reason before adjusting again.

Implementation lives in [backend/api/scheduling_eligibility](../../backend/api/scheduling_eligibility) (FastAPI route `POST /api/schedule-eligibility`, CLI `python -m scheduling_eligibility.cli`). Conflict/consecutive-request logic is deterministic Python (regression tested); Claude (Anthropic API) is only used to generate the plain-English summary shown to the CHW, to stay in the Claude sponsor track.
