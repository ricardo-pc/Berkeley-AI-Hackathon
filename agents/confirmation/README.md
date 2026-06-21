# Confirmation Agent

Sends an SMS confirmation once a prescription refill or reschedule has actually been executed — not for message relay (there's nothing to confirm to the patient; the message goes to the doctor, not back to them).

Implementation lives in [backend/api/confirmation](../../backend/api/confirmation): `templates.py` builds the message text (pure, no I/O — fully unit tested), `twilio_client.py` sends it via Twilio, `service.py` ties them together and refuses to send anything for `message_relay` or a failed executor result.

Chained automatically after the two executors that write the actual DB change:
- [backend/api/scheduler](../../backend/api/scheduler) (`POST /api/appointments`) — reschedule confirmations
- [backend/api/prescription_fulfillment](../../backend/api/prescription_fulfillment) (`POST /api/prescriptions`) — refill confirmations, the previously-missing executor for the refill side

A failed text send never undoes the booking/refill — both routes treat confirmation as best-effort and return `{"sent": false, "reason": "..."}` rather than erroring out.

Sponsor: Twilio. Add `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER` to `backend/api/.env`.

```bash
cd backend/api
python3 -m confirmation.cli --task-type prescription_refill --phone-number +14155550101 --result-json /path/to/result.json --pretty
```
