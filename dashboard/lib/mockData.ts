import type { Task } from "./types";

// Seed voicemails spanning all four lanes and every status, including the edge cases
// from the product spec (refill with no recent visit, repeated reschedules, worsening
// symptoms relay, chest-pain escalation). Swap this module for a real API later.
export const SEED_TASKS: Task[] = [
  {
    id: "vm-001",
    patient: { name: "Jane Doe", dob: "1957-04-02", phone: "(415) 555-0142" },
    type: "refill",
    status: "ready",
    summary: "Lisinopril 10mg refill — all checks passed",
    transcript:
      "Hi, this is Jane Doe. I'm out of my lisinopril, the 10 milligram one. Could you send a refill to the CVS on Geary? Thank you.",
    details: {
      Medication: "Lisinopril 10mg",
      "Last filled": "2026-03-18",
      Pharmacy: "CVS — Geary Blvd",
      Insurance: "Blue Shield PPO",
    },
    checks: [
      { label: "Visit within 6mo", pass: true, note: "Seen 3 months ago" },
      { label: "Upcoming visit", pass: true, note: "Annual on 2026-09-10" },
      { label: "Same dosage on file", pass: true },
      { label: "No conflicting meds", pass: true },
    ],
    action: { label: "Approve & refill", kind: "approve" },
  },
  {
    id: "vm-002",
    patient: { name: "Robert Ortiz", dob: "1968-11-21", phone: "(415) 555-0199" },
    type: "refill",
    status: "needs_info",
    summary: "Metformin refill — no visit in last 6 months",
    transcript:
      "Yeah hi, Robert Ortiz. I need my metformin refilled. Haven't been in for a while but I'm still taking it.",
    details: {
      Medication: "Metformin 500mg",
      "Last filled": "2025-08-02",
      "Last visit": "2025-06-30 (11mo ago)",
      Insurance: "Aetna HMO",
    },
    checks: [
      { label: "Visit within 6mo", pass: false, note: "Last seen 11 months ago" },
      { label: "Same dosage on file", pass: true },
      { label: "No conflicting meds", pass: true },
    ],
    action: { label: "Review", kind: "review" },
  },
  {
    id: "vm-003",
    patient: { name: "Amara Kim", dob: "1990-02-14", phone: "(415) 555-0177" },
    type: "refill",
    status: "done",
    summary: "Albuterol inhaler refill — approved",
    transcript:
      "Hi it's Amara Kim, my inhaler is almost empty, the albuterol. Can I get a refill please?",
    details: {
      Medication: "Albuterol HFA",
      "Last filled": "2026-02-28",
      Pharmacy: "Walgreens — Irving St",
      Insurance: "Kaiser",
    },
    checks: [
      { label: "Visit within 12mo", pass: true },
      { label: "Same dosage on file", pass: true },
      { label: "No conflicting meds", pass: true },
    ],
    action: { label: "Approve & refill", kind: "approve" },
  },
  {
    id: "vm-004",
    patient: { name: "Marcus Lee", dob: "1985-07-09", phone: "(415) 555-0123" },
    type: "schedule",
    status: "ready",
    summary: "Move follow-up to Tue 2:00 PM — slot open",
    transcript:
      "Hey, Marcus Lee. Something came up and I can't make my Thursday appointment. Can we move it to Tuesday afternoon if there's anything around 2?",
    details: {
      "Current appt": "Thu 2026-06-25, 9:00 AM",
      Requested: "Tue 2026-06-23, 2:00 PM",
      Provider: "Dr. Patel",
      "Visit type": "Follow-up (20 min)",
    },
    checks: [
      { label: "Slot available", pass: true, note: "Tue 2:00 PM open" },
      { label: "Provider available", pass: true },
      { label: "No reschedule pattern", pass: true },
    ],
    action: { label: "Approve & rebook", kind: "approve" },
  },
  {
    id: "vm-005",
    patient: { name: "Tina Vo", dob: "1972-12-30", phone: "(415) 555-0188" },
    type: "schedule",
    status: "pending",
    summary: "3rd reschedule in a row — confirm reason by phone",
    transcript:
      "Hi, Tina Vo again. I need to push my appointment back another week, something with work.",
    details: {
      "Current appt": "Fri 2026-06-27, 11:00 AM",
      Requested: "Following week, AM",
      Provider: "Dr. Nguyen",
      "Reschedule count": "3 consecutive",
    },
    checks: [
      { label: "Slot available", pass: true },
      {
        label: "No reschedule pattern",
        pass: false,
        note: "3rd consecutive request — call to confirm",
      },
    ],
    action: { label: "Call patient", kind: "call" },
  },
  {
    id: "vm-006",
    patient: { name: "Daniel Cho", dob: "1995-05-05", phone: "(415) 555-0166" },
    type: "schedule",
    status: "done",
    summary: "New-patient intake booked Mon 10:00 AM",
    transcript:
      "Hello, this is Daniel Cho, I'd like to set up a first appointment as a new patient. Mornings are best.",
    details: {
      Requested: "Mon 2026-06-22, 10:00 AM",
      Provider: "Dr. Patel",
      "Visit type": "New patient (40 min)",
    },
    checks: [
      { label: "Slot available", pass: true },
      { label: "Provider available", pass: true },
    ],
    action: { label: "Approve & book", kind: "approve" },
  },
  {
    id: "vm-007",
    patient: { name: "Priya Sharma", dob: "1980-09-18", phone: "(415) 555-0133" },
    type: "relay",
    status: "ready",
    summary: "Reports new side effects after dosage change → Dr. Patel",
    transcript:
      "Hi, Priya Sharma. Since the new dosage I've been getting dizzy in the mornings. I wanted the doctor to know.",
    details: {
      "Relay to": "Dr. Patel",
      Category: "Medication reaction",
      Urgency: "Routine — non-emergency",
    },
    checks: [
      { label: "Relevant to provider", pass: true, note: "Medication reaction" },
      { label: "Not an emergency", pass: true },
    ],
    action: { label: "Approve & relay", kind: "approve" },
  },
  {
    id: "vm-008",
    patient: { name: "George White", dob: "1949-01-11", phone: "(415) 555-0155" },
    type: "relay",
    status: "done",
    summary: "Requests wheelchair access for next visit — relayed",
    transcript:
      "This is George White. For my next visit I'll need wheelchair access, just wanted to let the office know ahead of time.",
    details: {
      "Relay to": "Front desk",
      Category: "Accommodation request",
      Urgency: "Routine",
    },
    checks: [{ label: "Relevant to provider", pass: true, note: "Accommodation" }],
    action: { label: "Approve & relay", kind: "approve" },
  },
  {
    id: "vm-009",
    patient: { name: "Susan Park", dob: "1963-03-27", phone: "(415) 555-0111" },
    type: "escalation",
    status: "escalated",
    summary: "Mentions chest pain — needs human review now",
    transcript:
      "Um, hi, this is Susan Park. I've been having some chest pain on and off since last night and I'm not sure what to do.",
    details: {
      "Trigger phrase": "“chest pain”",
      Category: "Possible emergency",
      "Received at": "08:42 AM",
    },
    checks: [
      { label: "Safety phrase detected", pass: false, note: "chest pain" },
      { label: "Cannot auto-process", pass: false },
    ],
    action: { label: "Open & call", kind: "open" },
  },
];
