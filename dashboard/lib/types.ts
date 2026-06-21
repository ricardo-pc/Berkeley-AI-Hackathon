export type RequestType = "refill" | "schedule" | "relay" | "escalation";

// Lifecycle of a voicemail task. `ready` = clears all eligibility checks and can be
// approved in one click. `needs_info`/`pending` await missing details or a human call.
// `escalated` bypasses automation. `done` = executed (or human-handled).
export type TaskStatus =
  | "ready"
  | "needs_info"
  | "pending"
  | "escalated"
  | "done";

export type ActionKind = "approve" | "review" | "call" | "open";

export interface EligibilityCheck {
  /** Short label for the rule the eligibility agent applied. */
  label: string;
  /** Whether the patient passed the check. */
  pass: boolean;
  /** Optional context shown next to a failed/notable check. */
  note?: string;
}

export interface Patient {
  name: string;
  dob: string;
  phone: string;
}

export interface Task {
  id: string;
  patient: Patient;
  type: RequestType;
  status: TaskStatus;
  /** One-line headline shown on the collapsed row. */
  summary: string;
  /** Mock voicemail transcription, revealed when the row is expanded. */
  transcript: string;
  /** Structured fields extracted by the Intake agent. */
  details: Record<string, string>;
  /** Per-agent eligibility results, rendered as chips. */
  checks: EligibilityCheck[];
  /** The single primary action offered for this task. */
  action: { label: string; kind: ActionKind };
}

export const REQUEST_TYPE_LABEL: Record<RequestType, string> = {
  refill: "Prescription Refills",
  schedule: "Schedule Changes",
  relay: "Message Relays",
  escalation: "Escalations",
};

export const REQUEST_TYPE_TAG: Record<RequestType, string> = {
  refill: "Refill",
  schedule: "Schedule",
  relay: "Relay",
  escalation: "Escalation",
};

// Display order of the lanes; escalations last so safety cases sit visually distinct.
export const REQUEST_TYPE_ORDER: RequestType[] = [
  "refill",
  "schedule",
  "relay",
  "escalation",
];
