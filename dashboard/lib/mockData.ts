import type { Task } from "./types";

// Seed rows shaped exactly like the Supabase `tasks` table the backend writes
// (task_type / status / agent_summary / agent_checks / proposed_action /
// flagged_reason). `transcript`, `patient_dob`, `patient_phone` are join-
// enriched (voicemails/patients) and faked here until Phase 2 wiring.
//
// Coverage: clean approvals (pending_approval), iffy gate-failures (escalated +
// actionable), non-actionable escalations incl. an emergency, a rejected
// follow-up, and a completed task.
export const SEED_TASKS: Task[] = [
  // --- Emergency (non-actionable) — sorts to the very top ---
  {
    id: "vm-009",
    patient_id: "p-009",
    patient_name: "Susan Park",
    task_type: "escalate",
    status: "escalated",
    agent_summary: "Susan Park needs manual review: Emergency symptoms mentioned in voicemail.",
    agent_checks: { triage: { emergency_signal: true } },
    proposed_action: { type: "escalate", reason: "emergency symptoms mentioned" },
    flagged_reason:
      "Emergency symptoms mentioned in voicemail — bypasses automation, call immediately.",
    created_at: "2026-06-21T08:42:00Z",
    transcript:
      "Um, hi, this is Susan Park. I've been having some chest pain on and off since last night and I'm not sure what to do.",
    patient_dob: "1963-03-27",
    patient_phone: "(415) 555-0111",
  },

  // --- Iffy: actionable refill, gate failed (stale visit) ---
  {
    id: "vm-002",
    patient_id: "p-002",
    patient_name: "Robert Ortiz",
    task_type: "prescription_refill",
    status: "escalated",
    agent_summary: "Robert Ortiz needs manual review: last visit exceeds 6 month eligibility window.",
    agent_checks: {
      intake_eval: { valid_json: true, missing_fields: [], request_type: "prescription_refill", patient_resolved: true },
      insurance: { valid: true, plan: "Aetna HMO" },
      prescription: {
        eligible: false,
        medication: "Metformin",
        dosage_match: true,
        requested_order: "metformin",
        active_dosage: "500mg",
        last_visit: "2025-06-30",
        recent_visit: false,
        conflict: false,
        conflict_medication: null,
      },
    },
    proposed_action: { type: "escalate", reason: "last visit exceeds 6 month eligibility window" },
    flagged_reason: "last visit exceeds 6 month eligibility window",
    created_at: "2026-06-21T07:50:00Z",
    transcript:
      "Yeah hi, Robert Ortiz. I need my metformin refilled. Haven't been in for a while but I'm still taking it.",
    patient_dob: "1968-11-21",
    patient_phone: "(415) 555-0199",
  },

  // --- Iffy: actionable reschedule, gate failed (3rd consecutive) ---
  {
    id: "vm-005",
    patient_id: "p-005",
    patient_name: "Tina Vo",
    task_type: "reschedule",
    status: "escalated",
    agent_summary: "Tina Vo needs manual review: repeated reschedules require a manual call.",
    agent_checks: {
      intake_eval: { valid_json: true, missing_fields: [], request_type: "reschedule", patient_resolved: true },
      insurance: { valid: true, plan: "Blue Shield PPO" },
      scheduling_eligibility: {
        conflict: false,
        conflict_reason: null,
        consecutive_reschedule_count: 3,
        requires_manual_call: true,
        alternative_slot_found: true,
      },
    },
    proposed_action: { type: "escalate", reason: "3 consecutive reschedules" },
    flagged_reason: "3rd consecutive reschedule — confirm reason by phone.",
    created_at: "2026-06-21T07:30:00Z",
    transcript:
      "Hi, Tina Vo again. I need to push my appointment back another week, something with work.",
    patient_dob: "1972-12-30",
    patient_phone: "(415) 555-0188",
  },

  // --- Non-actionable escalation: insurance not accepted ---
  {
    id: "vm-008",
    patient_id: "p-008",
    patient_name: "George White",
    task_type: "escalate",
    status: "escalated",
    agent_summary: "George White needs manual review: Insurance plan not accepted.",
    agent_checks: {
      intake_eval: { valid_json: true, missing_fields: [], request_type: "prescription_refill", patient_resolved: true },
      insurance: { valid: false, plan: "Out-of-network PPO", reason: "plan not accepted" },
    },
    proposed_action: { type: "escalate", reason: "insurance plan not accepted" },
    flagged_reason: "Insurance plan not accepted: Out-of-network PPO.",
    created_at: "2026-06-21T07:10:00Z",
    transcript:
      "This is George White, I wanted to refill my blood pressure medication please.",
    patient_dob: "1949-01-11",
    patient_phone: "(415) 555-0155",
  },

  // --- Clean approval: refill, gate passed ---
  {
    id: "vm-001",
    patient_id: "p-001",
    patient_name: "Jane Doe",
    task_type: "prescription_refill",
    status: "pending_approval",
    agent_summary: "Jane Doe is eligible for a Lisinopril refill.",
    agent_checks: {
      intake_eval: { valid_json: true, missing_fields: [], request_type: "prescription_refill", patient_resolved: true },
      insurance: { valid: true, plan: "Blue Shield PPO" },
      prescription: {
        eligible: true,
        medication: "Lisinopril",
        dosage_match: true,
        requested_order: "lisinopril 10mg",
        active_dosage: "10mg",
        last_visit: "2026-03-18",
        recent_visit: true,
        conflict: false,
        conflict_medication: null,
      },
    },
    proposed_action: {
      type: "prescription_refill",
      medication_name: "Lisinopril",
      dosage: "10mg",
      instructions: "Take one tablet daily",
      provider_id: "b1b2c3d4-0001-0001-0001-000000000001",
      patient_id: "p-001",
    },
    flagged_reason: null,
    created_at: "2026-06-21T06:55:00Z",
    transcript:
      "Hi, this is Jane Doe. I'm out of my lisinopril, the 10 milligram one. Could you send a refill to the CVS on Geary? Thank you.",
    patient_dob: "1957-04-02",
    patient_phone: "(415) 555-0142",
  },

  // --- Clean approval: reschedule, gate passed ---
  {
    id: "vm-004",
    patient_id: "p-004",
    patient_name: "Marcus Lee",
    task_type: "reschedule",
    status: "pending_approval",
    agent_summary: "Marcus Lee can be rescheduled to Tue Jun 23, 2:00 PM.",
    agent_checks: {
      intake_eval: { valid_json: true, missing_fields: [], request_type: "reschedule", patient_resolved: true },
      insurance: { valid: true, plan: "Kaiser" },
      scheduling_eligibility: {
        conflict: false,
        conflict_reason: null,
        consecutive_reschedule_count: 0,
        requires_manual_call: false,
        alternative_slot_found: null,
      },
    },
    proposed_action: {
      type: "reschedule",
      new_start: "2026-06-23T21:00:00Z",
      new_end: "2026-06-23T21:30:00Z",
      cancel_appointment_id: "appt-004",
      provider_id: "b1b2c3d4-0001-0001-0001-000000000001",
    },
    flagged_reason: null,
    created_at: "2026-06-21T06:40:00Z",
    transcript:
      "Hey, Marcus Lee. Something came up and I can't make my Thursday appointment. Can we move it to Tuesday afternoon if there's anything around 2?",
    patient_dob: "1985-07-09",
    patient_phone: "(415) 555-0123",
  },

  // --- Clean approval: relay, gate passed (flagged adverse reaction but approvable) ---
  {
    id: "vm-007",
    patient_id: "p-007",
    patient_name: "Priya Sharma",
    task_type: "message_relay",
    status: "pending_approval",
    agent_summary: "Priya Sharma's message is ready to relay to the provider.",
    agent_checks: {
      intake_eval: { valid_json: true, missing_fields: [], request_type: "message_relay", patient_resolved: true },
      insurance: { valid: true, plan: "Blue Shield PPO" },
      message: { adverse_reaction_reported: true },
    },
    proposed_action: {
      type: "message_relay",
      message: "Since the new dosage I've been getting dizzy in the mornings.",
      provider_id: "b1b2c3d4-0001-0001-0001-000000000001",
      patient_id: "p-007",
    },
    flagged_reason: null,
    created_at: "2026-06-21T06:20:00Z",
    transcript:
      "Hi, Priya Sharma. Since the new dosage I've been getting dizzy in the mornings. I wanted the doctor to know.",
    patient_dob: "1980-09-18",
    patient_phone: "(415) 555-0133",
  },

  // --- Already rejected: in the follow-up pile ---
  {
    id: "vm-006",
    patient_id: "p-006",
    patient_name: "Daniel Cho",
    task_type: "reschedule",
    status: "rejected",
    agent_summary: "Daniel Cho can be rescheduled to Mon Jun 22, 10:00 AM.",
    agent_checks: {
      intake_eval: { valid_json: true, missing_fields: [], request_type: "reschedule", patient_resolved: true },
      insurance: { valid: true, plan: "Aetna HMO" },
      scheduling_eligibility: {
        conflict: false,
        conflict_reason: null,
        consecutive_reschedule_count: 1,
        requires_manual_call: false,
        alternative_slot_found: null,
      },
    },
    proposed_action: {
      type: "reschedule",
      new_start: "2026-06-22T17:00:00Z",
      new_end: "2026-06-22T17:40:00Z",
      cancel_appointment_id: "appt-006",
      provider_id: "b1b2c3d4-0001-0001-0001-000000000001",
    },
    flagged_reason: null,
    chw_note: "No 10am slot actually free — need to call Daniel with alternatives.",
    reviewed_at: "2026-06-21T07:05:00Z",
    rejected_at: "2026-06-21T07:05:00Z",
    created_at: "2026-06-21T06:05:00Z",
    transcript:
      "Hello, this is Daniel Cho, I'd like to move my appointment to Monday morning if possible.",
    patient_dob: "1995-05-05",
    patient_phone: "(415) 555-0166",
  },

  // --- Already complete: in the done pile ---
  {
    id: "vm-003",
    patient_id: "p-003",
    patient_name: "Amara Kim",
    task_type: "prescription_refill",
    status: "complete",
    agent_summary: "Amara Kim is eligible for an Albuterol refill.",
    agent_checks: {
      intake_eval: { valid_json: true, missing_fields: [], request_type: "prescription_refill", patient_resolved: true },
      insurance: { valid: true, plan: "Kaiser" },
      prescription: {
        eligible: true,
        medication: "Albuterol",
        dosage_match: true,
        requested_order: "albuterol",
        active_dosage: "HFA 90mcg",
        last_visit: "2026-02-28",
        recent_visit: true,
        conflict: false,
        conflict_medication: null,
      },
    },
    proposed_action: {
      type: "prescription_refill",
      medication_name: "Albuterol",
      dosage: "HFA 90mcg",
      instructions: "Two puffs as needed",
      provider_id: "b1b2c3d4-0001-0001-0001-000000000001",
      patient_id: "p-003",
    },
    flagged_reason: null,
    reviewed_at: "2026-06-21T06:10:00Z",
    approved_at: "2026-06-21T06:10:00Z",
    created_at: "2026-06-21T05:55:00Z",
    transcript:
      "Hi it's Amara Kim, my inhaler is almost empty, the albuterol. Can I get a refill please?",
    patient_dob: "1990-02-14",
    patient_phone: "(415) 555-0177",
  },
];
