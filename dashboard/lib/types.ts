// Types mirror the Supabase `tasks` table written by the backend orchestrator
// (backend/orchestrator/main_loop.py). Keeping these aligned means wiring the
// dashboard to the DB is a thin row→Task mapper, not a reshape.

/** What kind of request the intake agent classified. The first three are
 *  "actionable" (a CHW approves/rejects); `escalate` is non-actionable and is
 *  handled manually ("Action taken"). */
export type TaskType =
  | "prescription_refill"
  | "reschedule"
  | "message_relay"
  | "escalate";

/** Lifecycle status as stored in the DB.
 *  - `pending_approval` — actionable item that cleared its eligibility gate.
 *  - `escalated` — gate failed (iffy actionable) OR a non-actionable escalation.
 *  - `rejected` — CHW rejected it; awaiting manual follow-up (our follow-up pile).
 *  - `complete` — approved/handled and done. */
export type TaskStatus =
  | "pending_approval"
  | "escalated"
  | "rejected"
  | "complete";

/** The concrete action the eligibility agent proposes. The CHW is approving
 *  exactly this. Shapes mirror each agent's `proposed_action`. */
export type ProposedAction =
  | {
      type: "prescription_refill";
      medication_name: string;
      dosage: string;
      instructions?: string;
      provider_id?: string;
      patient_id?: string;
    }
  | {
      type: "reschedule";
      new_start: string;
      new_end?: string;
      cancel_appointment_id?: string | null;
      provider_id?: string;
    }
  | {
      type: "message_relay";
      message: string;
      provider_id?: string;
      patient_id?: string;
    }
  | { type: "escalate"; reason?: string };

export interface Task {
  // --- columns straight from the `tasks` table ---
  id: string;
  patient_id: string | null;
  patient_name: string;
  task_type: TaskType;
  status: TaskStatus;
  agent_summary: string;
  agent_checks: Record<string, unknown>;
  proposed_action: ProposedAction | null;
  flagged_reason: string | null;
  created_at: string;

  // --- audit fields the dashboard writes on a decision ---
  chw_note?: string | null;
  reviewed_at?: string | null;
  approved_at?: string | null;
  rejected_at?: string | null;

  // --- enriched from joins (voicemails / patients) when wired; optional now ---
  transcript?: string;
  patient_dob?: string;
  patient_phone?: string;
}

/** A normalized eligibility check for display, flattened from `agent_checks`. */
export interface DisplayCheck {
  label: string;
  pass: boolean;
  note?: string;
}

/** Which review pile a task belongs in. */
export type Bucket = "to_review" | "follow_up" | "done";

export const TASK_TYPE_TAG: Record<TaskType, string> = {
  prescription_refill: "Refill",
  reschedule: "Schedule",
  message_relay: "Relay",
  escalate: "Escalation",
};
