# Voicemail Triage System — Database Reference
---
## 1. Overview
Seven tables, created in this order (foreign keys require it):
| # | Table | Purpose |
|---|---|---|
| 1 | `patients` | People who call in. Identity, contact, insurance. |
| 2 | `voicemails` | Raw inbound calls. Audio path, transcript, intent, status. |
| 3 | `providers` | Doctors. Availability windows used for scheduling. |
| 4 | `appointments` | The clinic calendar. Patient + provider + time slot. |
| 5 | `prescriptions` | Medication history. Used to verify refill eligibility. |
| 6 | `tasks` | Central dashboard table. One row per voicemail request. |
| 7 | `messages` | Message relay requests from patient to provider. |
---
## 2. Table Schemas
### 2.1 patients
Every other table either references this directly or resolves to it through a join. The Intake Agent reads this to match a caller's name and date of birth to an existing record.
| Column | Type | Description | Notes |
|---|---|---|---|
| `id` | uuid | Primary key | Auto-generated |
| `first_name` | text | First name | |
| `last_name` | text | Last name | |
| `date_of_birth` | date | Patient DOB | Used by Intake Agent to match identity |
| `phone` | text | Contact number | |
| `insurance_plan` | text | Plan name | e.g. Blue Cross PPO |
| `insurance_id` | text | Member ID | From patient's insurance card |
| `insurance_valid` | boolean | Accepted by clinic | Set by Eligibility Agent |
| `created_at` | timestamptz | Row created | Auto-generated |
```sql
create table patients (
  id                uuid primary key default gen_random_uuid(),
  first_name        text not null,
  last_name         text not null,
  date_of_birth     date not null,
  phone             text,
  insurance_plan    text,
  insurance_id      text,
  insurance_valid   boolean default false,
  created_at        timestamptz default now()
);
```
---
### 2.2 voicemails
References `patients`. `patient_id` is intentionally nullable — it starts NULL when a voicemail arrives and is populated only after the Intake Agent resolves the caller's identity.
| Column | Type | Description | Notes |
|---|---|---|---|
| `id` | uuid | Primary key | Auto-generated |
| `audio_url` | text | Path to audio file | Uploaded by CHW before processing |
| `transcript` | text | Deepgram output | Raw transcription text |
| `status` | text | Processing status | `queued` \| `processing` \| `complete` \| `flagged` |
| `intent` | text | Detected request type | `prescription_refill` \| `reschedule` \| `message_relay` \| `unknown` |
| `patient_id` | uuid | FK → patients.id | NULL until Intake Agent resolves identity |
| `created_at` | timestamptz | Row created | Auto-generated |
```sql
create table voicemails (
  id          uuid primary key default gen_random_uuid(),
  audio_url   text,
  transcript  text,
  status      text default 'queued',
  intent      text,
  patient_id  uuid references patients(id),
  created_at  timestamptz default now()
);
```
---
### 2.3 providers
Stores doctors and their weekly availability as JSONB. The Scheduling Agent reads this to determine what time slots are possible before checking `appointments` for conflicts.
| Column | Type | Description | Notes |
|---|---|---|---|
| `id` | uuid | Primary key | Auto-generated |
| `name` | text | Doctor's name | e.g. Dr. Sarah Lee |
| `specialty` | text | Medical specialty | e.g. Family Medicine |
| `availability` | jsonb | Working hours per day | Used by Scheduling Agent |
| `created_at` | timestamptz | Row created | Auto-generated |
```sql
create table providers (
  id            uuid primary key default gen_random_uuid(),
  name          text not null,
  specialty     text,
  availability  jsonb default '{
    "mon": ["09:00","17:00"],
    "tue": ["09:00","17:00"],
    "wed": ["09:00","17:00"],
    "thu": ["09:00","17:00"],
    "fri": ["09:00","17:00"]
  }',
  created_at    timestamptz default now()
);
```
---
### 2.4 appointments
The clinic calendar. Links a patient to a provider at a specific time. The Scheduling Agent reads this to detect conflicts and writes to it when a reschedule is approved. The Prescription Agent also reads this to check whether a patient has visited within the required 6/12-month window.
| Column | Type | Description | Notes |
|---|---|---|---|
| `id` | uuid | Primary key | Auto-generated |
| `patient_id` | uuid | FK → patients.id | Which patient |
| `provider_id` | uuid | FK → providers.id | Which doctor |
| `start_time` | timestamptz | Appointment start | |
| `end_time` | timestamptz | Appointment end | |
| `visit_type` | text | Type of visit | `follow_up` \| `new_patient` \| `prescription_review` |
| `status` | text | Appointment status | `scheduled` \| `cancelled` \| `rescheduled` \| `no_show` |
| `created_at` | timestamptz | Row created | Auto-generated |
```sql
create table appointments (
  id            uuid primary key default gen_random_uuid(),
  patient_id    uuid references patients(id),
  provider_id   uuid references providers(id),
  start_time    timestamptz not null,
  end_time      timestamptz not null,
  visit_type    text,
  status        text default 'scheduled',
  created_at    timestamptz default now()
);
```
---
### 2.5 prescriptions
Medication history per patient. The Prescription Agent reads this to verify: the medication was previously prescribed at the same dosage, the prescribing doctor matches, and no conflicting medications are currently active.
| Column | Type | Description | Notes |
|---|---|---|---|
| `id` | uuid | Primary key | Auto-generated |
| `patient_id` | uuid | FK → patients.id | Which patient |
| `provider_id` | uuid | FK → providers.id | Who prescribed it |
| `medication_name` | text | Drug name | e.g. Lisinopril |
| `dosage` | text | Dosage amount | e.g. 10mg |
| `instructions` | text | How to take it | e.g. once daily with food |
| `prescribed_at` | timestamptz | When prescribed | Used to check 6/12 month window |
| `active` | boolean | Still active | false = discontinued |
| `created_at` | timestamptz | Row created | Auto-generated |
```sql
create table prescriptions (
  id              uuid primary key default gen_random_uuid(),
  patient_id      uuid references patients(id),
  provider_id     uuid references providers(id),
  medication_name text not null,
  dosage          text,
  instructions    text,
  prescribed_at   timestamptz default now(),
  active          boolean default true,
  created_at      timestamptz default now()
);
```
---
### 2.6 tasks
The most important table. The dashboard reads entirely from this. One row per voicemail request. Stores the full agent reasoning trail in `agent_checks` (JSONB) and the executable action in `proposed_action` (JSONB). When a CHW clicks approve, the backend reads `proposed_action.type` and executes exactly one write against the relevant table.
| Column | Type | Description | Notes |
|---|---|---|---|
| `id` | uuid | Primary key | Auto-generated |
| `voicemail_id` | uuid | FK → voicemails.id | Source voicemail |
| `patient_id` | uuid | FK → patients.id | Resolved patient |
| `task_type` | text | What was requested | `prescription_refill` \| `reschedule` \| `message_relay` \| `escalate` |
| `status` | text | Task status | `pending_approval` \| `approved` \| `rejected` \| `escalated` \| `complete` |
| `agent_summary` | text | Plain English recommendation | CHW reads this before clicking approve |
| `agent_checks` | jsonb | Structured agent results | Insurance, prescription, scheduling checks |
| `proposed_action` | jsonb | What executes on approval | Read by backend to perform DB writes |
| `flagged_reason` | text | Why it was escalated | Only populated when status = escalated |
| `approved_by` | text | CHW who approved | Staff name or ID |
| `approved_at` | timestamptz | When approved | |
| `created_at` | timestamptz | Row created | Auto-generated |
**Example `agent_checks` (prescription refill):**
```json
{
  "insurance": { "valid": true, "plan": "Blue Cross PPO" },
  "prescription": {
    "eligible": true,
    "medication": "Lisinopril",
    "dosage_match": true,
    "last_visit": "2026-01-10",
    "conflict": true,
    "conflict_medication": "Amlodipine"
  }
}
```
**Example `proposed_action` (reschedule):**
```json
{
  "type": "reschedule",
  "cancel_appointment_id": "c1b2c3d4-0004-0004-0004-000000000004",
  "new_start": "2026-06-25T09:00:00+00:00",
  "new_end": "2026-06-25T09:30:00+00:00",
  "provider_id": "b1b2c3d4-0001-0001-0001-000000000001"
}
```
```sql
create table tasks (
  id              uuid primary key default gen_random_uuid(),
  voicemail_id    uuid references voicemails(id),
  patient_id      uuid references patients(id),
  task_type       text,
  status          text default 'pending_approval',
  agent_summary   text,
  agent_checks    jsonb,
  proposed_action jsonb,
  flagged_reason  text,
  approved_by     text,
  approved_at     timestamptz,
  created_at      timestamptz default now()
);
```
---
### 2.7 messages
Message relay requests from patient to provider. `task_id` is NULL in seed data — populated at runtime when the Message Relay Agent creates a task and links it back. `delivered` is set to true on CHW approval.
| Column | Type | Description | Notes |
|---|---|---|---|
| `id` | uuid | Primary key | Auto-generated |
| `task_id` | uuid | FK → tasks.id | NULL in seed, populated at runtime |
| `patient_id` | uuid | FK → patients.id | Sender |
| `provider_id` | uuid | FK → providers.id | Recipient doctor |
| `message_body` | text | Message content | Extracted from voicemail transcript |
| `delivered` | boolean | Delivered to doctor | Set to true on CHW approval |
| `created_at` | timestamptz | Row created | Auto-generated |
```sql
create table messages (
  id           uuid primary key default gen_random_uuid(),
  task_id      uuid references tasks(id),
  patient_id   uuid references patients(id),
  provider_id  uuid references providers(id),
  message_body text not null,
  delivered    boolean default false,
  created_at   timestamptz default now()
);
```
---
## 3. How Tables Connect
```
patients
    │
    ├──► voicemails.patient_id
    ├──► appointments.patient_id
    ├──► prescriptions.patient_id
    ├──► tasks.patient_id
    └──► messages.patient_id
providers
    │
    ├──► appointments.provider_id
    ├──► prescriptions.provider_id
    └──► messages.provider_id
voicemails
    └──► tasks.voicemail_id
tasks
    └──► messages.task_id
```
`patients` never references `providers` directly. The connection always goes through `appointments`, `prescriptions`, or `messages`.
---
## 4. Agent → Table Map
| Agent | Reads | Writes |
|---|---|---|
| Intake Agent | `voicemails`, `patients` | `voicemails.transcript`, `voicemails.patient_id`, `voicemails.intent` |
| Eligibility Agent | `patients.insurance_*` | `tasks.agent_checks` (insurance result) |
| Prescription Agent | `prescriptions`, `appointments` | `tasks.agent_checks` (refill eligibility) |
| Scheduling Agent | `appointments`, `providers.availability` | `tasks.proposed_action` (suggested slot) |
| Message Relay Agent | `voicemails.transcript` | `messages` row, `tasks.proposed_action` |
| Triage Sentinel | `voicemails.transcript` | `tasks.status = escalated`, `tasks.flagged_reason` |
| Summary Agent | `tasks` (all rows) | Read only — renders dashboard |
Agents only write to `tasks`, `voicemails`, and `messages`. Writes to `appointments` and `prescriptions` happen only on CHW approval.
---
## 5. Seed Data
### Patients & scenarios
| Patient | Insurance | Medication | Demo Scenario |
|---|---|---|---|
| Maria Gonzalez | Blue Cross PPO ✓ | Lisinopril + Amlodipine | Eligible refill — conflict warning (drug interaction) |
| James Okafor | Aetna HMO ✓ | Metformin | Ineligible — last visit Nov 2024, outside 6-month window |
| Linda Chen | Kaiser Permanente ✗ | — | Reschedule blocked — insurance not accepted |
| Robert Martinez | United Healthcare ✓ | Atorvastatin | Reschedule — slot conflict Jun 24, agent proposes Jun 25 |
| Priya Sharma | Blue Cross PPO ✓ | Sertraline | Message relay — adverse reaction (dizziness, nausea) |
### Providers
- **Dr. Sarah Lee** — Family Medicine — Mon–Fri 9am–5pm
- **Dr. James Patel** — Internal Medicine — Mon/Wed/Fri 8am–4pm (Fri until 1pm)
### Key conflict rows
- Maria has both Lisinopril and Amlodipine active → triggers drug interaction warning
- Robert requests Jun 24 3pm → that slot is pre-seeded as taken → agent proposes Jun 25 9am
- James's last visit was Nov 2024 → outside the 6-month window → refill ineligible
- Linda's insurance (Kaiser Permanente) is seeded as invalid → blocks reschedule before scheduling logic runs
### Full seed SQL
```sql
-- PATIENTS
insert into patients (id, first_name, last_name, date_of_birth, phone, insurance_plan, insurance_id, insurance_valid) values
  ('a1b2c3d4-0001-0001-0001-000000000001', 'Maria',   'Gonzalez', '1978-03-12', '415-555-0101', 'Blue Cross PPO',    'BC-882341', true),
  ('a1b2c3d4-0002-0002-0002-000000000002', 'James',   'Okafor',   '1965-07-24', '510-555-0182', 'Aetna HMO',         'AE-445521', true),
  ('a1b2c3d4-0003-0003-0003-000000000003', 'Linda',   'Chen',     '1990-11-05', '628-555-0193', 'Kaiser Permanente', 'KP-119834', false),
  ('a1b2c3d4-0004-0004-0004-000000000004', 'Robert',  'Martinez', '1952-01-30', '415-555-0174', 'United Healthcare', 'UH-773920', true),
  ('a1b2c3d4-0005-0005-0005-000000000005', 'Priya',   'Sharma',   '1988-09-18', '510-555-0165', 'Blue Cross PPO',    'BC-991234', true);
-- PROVIDERS
insert into providers (id, name, specialty, availability) values
  ('b1b2c3d4-0001-0001-0001-000000000001', 'Dr. Sarah Lee',   'Family Medicine',   '{"mon":["09:00","17:00"],"tue":["09:00","17:00"],"wed":["09:00","17:00"],"thu":["09:00","17:00"],"fri":["09:00","17:00"]}'),
  ('b1b2c3d4-0002-0002-0002-000000000002', 'Dr. James Patel', 'Internal Medicine', '{"mon":["08:00","16:00"],"wed":["08:00","16:00"],"fri":["08:00","13:00"]}');
-- APPOINTMENTS
insert into appointments (id, patient_id, provider_id, start_time, end_time, visit_type, status) values
  -- Maria: recent visit (satisfies refill) + upcoming visit
  ('c1b2c3d4-0001-0001-0001-000000000001', 'a1b2c3d4-0001-0001-0001-000000000001', 'b1b2c3d4-0001-0001-0001-000000000001', '2026-01-10 10:00:00+00', '2026-01-10 10:30:00+00', 'follow_up', 'scheduled'),
  ('c1b2c3d4-0002-0002-0002-000000000002', 'a1b2c3d4-0001-0001-0001-000000000001', 'b1b2c3d4-0001-0001-0001-000000000001', '2026-09-15 10:00:00+00', '2026-09-15 10:30:00+00', 'follow_up', 'scheduled'),
  -- James: last visit too old (fails refill check)
  ('c1b2c3d4-0003-0003-0003-000000000003', 'a1b2c3d4-0002-0002-0002-000000000002', 'b1b2c3d4-0002-0002-0002-000000000002', '2024-11-20 09:00:00+00', '2024-11-20 09:30:00+00', 'follow_up', 'scheduled'),
  -- Robert: existing slot that will cause conflict in demo
  ('c1b2c3d4-0004-0004-0004-000000000004', 'a1b2c3d4-0004-0004-0004-000000000004', 'b1b2c3d4-0001-0001-0001-000000000001', '2026-06-24 15:00:00+00', '2026-06-24 15:30:00+00', 'new_patient', 'scheduled'),
  -- Priya: upcoming visit only
  ('c1b2c3d4-0005-0005-0005-000000000005', 'a1b2c3d4-0005-0005-0005-000000000005', 'b1b2c3d4-0001-0001-0001-000000000001', '2026-07-08 11:00:00+00', '2026-07-08 11:30:00+00', 'prescription_review', 'scheduled');
-- PRESCRIPTIONS
insert into prescriptions (id, patient_id, provider_id, medication_name, dosage, instructions, prescribed_at, active) values
  -- Maria: Lisinopril (eligible) + Amlodipine (conflict trigger)
  ('d1b2c3d4-0001-0001-0001-000000000001', 'a1b2c3d4-0001-0001-0001-000000000001', 'b1b2c3d4-0001-0001-0001-000000000001', 'Lisinopril',   '10mg',  'once daily with food',     '2026-01-10 10:30:00+00', true),
  ('d1b2c3d4-0002-0002-0002-000000000002', 'a1b2c3d4-0001-0001-0001-000000000001', 'b1b2c3d4-0001-0001-0001-000000000001', 'Amlodipine',   '5mg',   'once daily',               '2026-01-10 10:30:00+00', true),
  -- James: too old (ineligible)
  ('d1b2c3d4-0003-0003-0003-000000000003', 'a1b2c3d4-0002-0002-0002-000000000002', 'b1b2c3d4-0002-0002-0002-000000000002', 'Metformin',    '500mg', 'twice daily with meals',   '2024-11-20 09:30:00+00', true),
  -- Robert: eligible
  ('d1b2c3d4-0004-0004-0004-000000000004', 'a1b2c3d4-0004-0004-0004-000000000004', 'b1b2c3d4-0001-0001-0001-000000000001', 'Atorvastatin', '20mg',  'once daily at bedtime',    '2026-03-05 14:00:00+00', true),
  -- Priya: active
  ('d1b2c3d4-0005-0005-0005-000000000005', 'a1b2c3d4-0005-0005-0005-000000000005', 'b1b2c3d4-0001-0001-0001-000000000001', 'Sertraline',   '50mg',  'once daily in the morning','2026-02-18 11:00:00+00', true);
-- VOICEMAILS
insert into voicemails (id, audio_url, transcript, status, intent, patient_id) values
  ('e1b2c3d4-0001-0001-0001-000000000001', '/voicemails/maria_refill.mp3',      'Hi this is Maria Gonzalez, date of birth March 12 1978. I am calling to request a refill for my Lisinopril 10mg. My number is 415-555-0101. Thank you.',                                                                          'complete', 'prescription_refill', 'a1b2c3d4-0001-0001-0001-000000000001'),
  ('e1b2c3d4-0002-0002-0002-000000000002', '/voicemails/james_refill.mp3',      'Hey this is James Okafor, July 24 1965. I need a refill on my Metformin 500mg please. You can reach me at 510-555-0182.',                                                                                                          'complete', 'prescription_refill', 'a1b2c3d4-0002-0002-0002-000000000002'),
  ('e1b2c3d4-0003-0003-0003-000000000003', '/voicemails/linda_reschedule.mp3',  'Hi my name is Linda Chen, November 5 1990. I would like to reschedule my appointment to June 24th at 3pm if possible. My number is 628-555-0193.',                                                                                 'complete', 'reschedule',          'a1b2c3d4-0003-0003-0003-000000000003'),
  ('e1b2c3d4-0004-0004-0004-000000000004', '/voicemails/robert_reschedule.mp3', 'This is Robert Martinez, January 30 1952. I need to move my appointment to June 24th around 3 in the afternoon with Dr. Lee. My number is 415-555-0174.',                                                                          'complete', 'reschedule',          'a1b2c3d4-0004-0004-0004-000000000004'),
  ('e1b2c3d4-0005-0005-0005-000000000005', '/voicemails/priya_message.mp3',     'Hi this is Priya Sharma, September 18 1988. I just wanted to let Dr. Lee know that I have been feeling really dizzy and nauseous since I started the Sertraline three days ago. Please let her know. My number is 510-555-0165.', 'complete', 'message_relay',       'a1b2c3d4-0005-0005-0005-000000000005');
-- TASKS
insert into tasks (id, voicemail_id, patient_id, task_type, status, agent_summary, agent_checks, proposed_action) values
  ('f1b2c3d4-0001-0001-0001-000000000001',
   'e1b2c3d4-0001-0001-0001-000000000001', 'a1b2c3d4-0001-0001-0001-000000000001',
   'prescription_refill', 'pending_approval',
   'Maria Gonzalez is eligible for a Lisinopril refill. Recent visit Jan 10 2026 confirmed. Note: patient is also on Amlodipine — possible interaction, physician review recommended.',
   '{"insurance":{"valid":true,"plan":"Blue Cross PPO"},"prescription":{"eligible":true,"medication":"Lisinopril","dosage_match":true,"last_visit":"2026-01-10","conflict":true,"conflict_medication":"Amlodipine"}}',
   '{"type":"prescription_refill","medication_name":"Lisinopril","dosage":"10mg","instructions":"once daily with food","provider_id":"b1b2c3d4-0001-0001-0001-000000000001","patient_id":"a1b2c3d4-0001-0001-0001-000000000001"}'
  ),
  ('f1b2c3d4-0002-0002-0002-000000000002',
   'e1b2c3d4-0002-0002-0002-000000000002', 'a1b2c3d4-0002-0002-0002-000000000002',
   'prescription_refill', 'escalated',
   'James Okafor requested a Metformin refill. Last visit was November 2024 — outside the 6-month window. Patient must schedule a visit before refill can be approved.',
   '{"insurance":{"valid":true,"plan":"Aetna HMO"},"prescription":{"eligible":false,"medication":"Metformin","dosage_match":true,"last_visit":"2024-11-20","conflict":false,"reason":"last visit exceeds 6 month window"}}',
   '{"type":"escalate","reason":"last visit exceeds 6 month eligibility window"}'
  ),
  ('f1b2c3d4-0003-0003-0003-000000000003',
   'e1b2c3d4-0003-0003-0003-000000000003', 'a1b2c3d4-0003-0003-0003-000000000003',
   'reschedule', 'escalated',
   'Linda Chen requested a reschedule to June 24 at 3pm. Insurance flagged as invalid — Kaiser Permanente not accepted at this clinic. Cannot proceed until insurance is resolved.',
   '{"insurance":{"valid":false,"plan":"Kaiser Permanente","reason":"plan not accepted"},"scheduling":{"conflict":false,"requested_slot":"2026-06-24T15:00:00+00:00"}}',
   '{"type":"escalate","reason":"insurance plan not accepted"}'
  ),
  ('f1b2c3d4-0004-0004-0004-000000000004',
   'e1b2c3d4-0004-0004-0004-000000000004', 'a1b2c3d4-0004-0004-0004-000000000004',
   'reschedule', 'pending_approval',
   'Robert Martinez requested June 24 at 3pm with Dr. Lee. That slot is already booked. Next available slot is June 25 at 9am — proposed as alternative.',
   '{"insurance":{"valid":true,"plan":"United Healthcare"},"scheduling":{"conflict":true,"requested_slot":"2026-06-24T15:00:00+00:00","conflict_reason":"slot already booked","proposed_slot":"2026-06-25T09:00:00+00:00"}}',
   '{"type":"reschedule","cancel_appointment_id":"c1b2c3d4-0004-0004-0004-000000000004","new_start":"2026-06-25T09:00:00+00:00","new_end":"2026-06-25T09:30:00+00:00","provider_id":"b1b2c3d4-0001-0001-0001-000000000001"}'
  ),
  ('f1b2c3d4-0005-0005-0005-000000000005',
   'e1b2c3d4-0005-0005-0005-000000000005', 'a1b2c3d4-0005-0005-0005-000000000005',
   'message_relay', 'pending_approval',
   'Priya Sharma reports dizziness and nausea since starting Sertraline 3 days ago. Message qualifies for relay to Dr. Lee — adverse medication reaction.',
   '{"insurance":{"valid":true,"plan":"Blue Cross PPO"},"message":{"qualifies":true,"reason":"adverse medication reaction reported"}}',
   '{"type":"message_relay","provider_id":"b1b2c3d4-0001-0001-0001-000000000001","patient_id":"a1b2c3d4-0005-0005-0005-000000000005","message":"Patient reports dizziness and nausea since starting Sertraline 3 days ago. Requests callback."}'
  );
-- MESSAGES
insert into messages (task_id, patient_id, provider_id, message_body, delivered) values
  ('f1b2c3d4-0005-0005-0005-000000000005',
   'a1b2c3d4-0005-0005-0005-000000000005',
   'b1b2c3d4-0001-0001-0001-000000000001',
   'Patient reports dizziness and nausea since starting Sertraline 3 days ago. Requests callback.',
   false);
```
---
## 6. Supabase Configuration
| Setting | Value | Reason |
|---|---|---|
| Data API | Enabled | Required for supabase-js |
| RLS | Disabled | Agents use service role key server-side |
| Auto-expose new tables | Disabled | Control access manually |
| Auto RLS | Disabled | Adds friction with no security benefit at demo scale |
Use the **service role key** in all agent/backend calls. Never expose it client-side. All agent logic runs through server-side API routes.
---
## 7. Approval Flow
When a CHW clicks approve, the backend reads `tasks.proposed_action.type` and executes one write:
| `proposed_action.type` | What executes |
|---|---|
| `prescription_refill` | INSERT new row into `prescriptions` |
| `reschedule` | UPDATE existing `appointments` row to `rescheduled` + INSERT new row at proposed slot |
| `message_relay` | UPDATE `messages.delivered = true` |
| `escalate` | No write — stays in flagged queue for manual CHW action |
After any approval: `tasks.status` → `complete`, `tasks.approved_by` and `tasks.approved_at` populated. Dashboard re-queries `tasks` to reflect new state.
