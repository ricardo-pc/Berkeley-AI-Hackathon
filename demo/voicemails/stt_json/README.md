# Mock Deepgram STT JSON

These files mimic Deepgram pre-recorded speech-to-text responses and can be fed directly into the Intake Agent CLI:

```bash
backend/api/.venv/bin/python -m agents.intake.cli demo/voicemails/stt_json/01_maria_gonzalez_refill_valid.json --pretty
```

They intentionally mix seeded database patients from `docs/database/README.md` with invalid or incomplete callers so downstream eligibility agents can be tested.

## Cases

- `01_maria_gonzalez_refill_valid.json` — seeded patient, accepted insurance, refill request with matching seeded medication.
- `02_james_okafor_refill_old_visit.json` — seeded patient, accepted insurance, refill request that should fail later because his last visit is too old.
- `03_linda_chen_reschedule_invalid_insurance.json` — seeded patient, Kaiser insurance should fail insurance eligibility.
- `04_robert_martinez_reschedule_conflict.json` — seeded patient, requests the pre-seeded conflicting June 24 3pm slot.
- `05_priya_sharma_message_relay_adverse_reaction.json` — seeded patient, message relay/adverse medication reaction.
- `06_unknown_patient_refill_not_in_db.json` — not in seeded patients, useful for patient-match failure.
- `07_missing_dob_and_insurance_reschedule.json` — missing required identity/insurance details.
- `08_emergency_symptoms_escalation.json` — urgent symptoms, should eventually force escalation/human review.
- `09_maria_gonzalez_dosage_mismatch.json` — seeded patient, medication exists but requested dosage does not match seeded prescription.
- `10_maria_gonzalez_refill_and_message_relay.json` — seeded patient with two requests in one voicemail: refill plus doctor-message relay.
