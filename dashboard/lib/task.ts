// Pure derivations over a Task: bucketing, actionability, urgency ordering,
// and presenters that turn the DB's nested `agent_checks` / `proposed_action`
// JSON into something a CHW can read at a glance.

import type { Bucket, DisplayCheck, ProposedAction, Task } from "./types";

const ACTIONABLE_TYPES = new Set(["prescription_refill", "reschedule", "message_relay"]);

/** Demo "today" — matches the backend REFERENCE_NOW so ages/dates line up. */
export const NOW = new Date("2026-06-21T00:00:00Z");

export function bucketOf(task: Task): Bucket {
  if (task.status === "complete") return "done";
  if (task.status === "rejected") return "follow_up";
  return "to_review"; // pending_approval | escalated
}

/** Actionable = a CHW approves/rejects it. Non-actionable = manual handling. */
export function isActionable(task: Task): boolean {
  return ACTIONABLE_TYPES.has(task.task_type);
}

/** Iffy: an actionable item whose eligibility gate failed (status escalated).
 *  The CHW can still approve or reject, ideally with an audit note. */
export function isIffy(task: Task): boolean {
  return isActionable(task) && task.status === "escalated";
}

/** Emergency triage signal (chest pain, etc.) — bypasses automation, top of queue. */
export function isEmergency(task: Task): boolean {
  const triage = task.agent_checks?.triage as { emergency_signal?: boolean } | undefined;
  return Boolean(triage?.emergency_signal);
}

/** How the CHW resolves the task once reviewed. */
export type DecisionMode = "approve_reject" | "action_taken";

export function decisionModeOf(task: Task): DecisionMode {
  return isActionable(task) ? "approve_reject" : "action_taken";
}

/** Approve button copy — names the concrete action it triggers (refill/rebook/relay)
 *  so the CHW isn't clicking a blind "Approve" before reading the detail panel. */
const APPROVE_LABEL: Record<Task["task_type"], string> = {
  prescription_refill: "Approve & refill",
  reschedule: "Approve & rebook",
  message_relay: "Approve & relay",
  escalate: "Approve",
};

export function approveLabel(task: Task): string {
  // The eligibility gate failed without proposing a concrete refill/reschedule
  // (proposed_action.type === "escalate") — approving just closes the task out,
  // it doesn't run the agent's normal action, so don't promise one.
  if (task.proposed_action?.type === "escalate") return "Mark handled";
  return APPROVE_LABEL[task.task_type] ?? "Approve";
}

/** Queue ordering: emergencies first, then iffy (needs judgment), then other
 *  manual escalations, then clean approvals — oldest first within a tier. */
export function reviewPriority(task: Task): number {
  if (isEmergency(task)) return 0;
  if (isIffy(task)) return 1;
  if (!isActionable(task)) return 2; // non-emergency manual escalation
  return 3; // clean pending_approval
}

export function sortForReview(tasks: Task[]): Task[] {
  return [...tasks].sort(
    (a, b) =>
      reviewPriority(a) - reviewPriority(b) ||
      a.created_at.localeCompare(b.created_at),
  );
}

export type DecisionTone = "approve" | "reject" | "handle";
export interface DecisionLabel {
  label: string;
  tone: DecisionTone;
}

/** What decision a *decided* task represents, for the history log. */
export function decisionLabel(task: Task): DecisionLabel {
  if (task.status === "rejected") return { label: "Rejected", tone: "reject" };
  if (task.status === "complete") {
    if (task.rejected_at) return { label: "Rejected · closed", tone: "reject" };
    if (task.task_type === "escalate") return { label: "Handled", tone: "handle" };
    return { label: "Approved", tone: "approve" };
  }
  return { label: "—", tone: "approve" };
}

/** When the decision happened (best available timestamp). */
export function decisionTime(task: Task): string {
  return task.reviewed_at ?? task.approved_at ?? task.rejected_at ?? task.created_at;
}

/** Tasks that have been acted on — the history log's contents. */
export function isDecided(task: Task): boolean {
  return task.status === "complete" || task.status === "rejected";
}

export function ageFromDob(dob?: string): number | null {
  if (!dob) return null;
  const birth = new Date(dob);
  let age = NOW.getUTCFullYear() - birth.getUTCFullYear();
  const m = NOW.getUTCMonth() - birth.getUTCMonth();
  if (m < 0 || (m === 0 && NOW.getUTCDate() < birth.getUTCDate())) age -= 1;
  return age;
}

function formatDateTime(iso?: string): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

/** One human line describing exactly what Approve will execute. */
export function describeProposedAction(action: ProposedAction | null): string {
  if (!action) return "No action proposed.";
  switch (action.type) {
    case "prescription_refill":
      return `Send refill — ${action.medication_name} ${action.dosage}${
        action.instructions ? ` (${action.instructions})` : ""
      }`;
    case "reschedule":
      return `Rebook to ${formatDateTime(action.new_start)}${
        action.cancel_appointment_id ? " — cancels current appointment" : ""
      }`;
    case "message_relay":
      return `Relay to provider: “${action.message}”`;
    case "escalate":
      return `Manual review required${action.reason ? ` — ${action.reason}` : ""}`;
  }
}

/** Flatten the backend's nested `agent_checks` into readable pass/fail chips.
 *  Knows the shapes each eligibility agent writes; unknown keys are ignored. */
export function presentChecks(agentChecks: Record<string, unknown>): DisplayCheck[] {
  const out: DisplayCheck[] = [];
  const c = agentChecks ?? {};

  const triage = c.triage as { emergency_signal?: boolean } | undefined;
  if (triage?.emergency_signal) {
    out.push({ label: "Emergency signal", pass: false, note: "Bypasses automation — call now" });
  }

  const intake = c.intake_eval as { missing_fields?: string[] } | undefined;
  if (intake) {
    const missing = intake.missing_fields ?? [];
    out.push({
      label: "Intake complete",
      pass: missing.length === 0,
      note: missing.length ? `Missing: ${missing.join(", ")}` : undefined,
    });
  }

  const insurance = c.insurance as { valid?: boolean; reason?: string } | undefined;
  if (insurance) {
    out.push({
      label: "Insurance accepted",
      pass: Boolean(insurance.valid),
      note: insurance.reason,
    });
  }

  const rx = c.prescription as
    | {
        dosage_match?: boolean;
        recent_visit?: boolean;
        last_visit?: string | null;
        requested_order?: string;
        active_dosage?: string;
        conflict?: boolean;
        conflict_medication?: string | null;
      }
    | undefined;
  if (rx) {
    out.push({
      label: "Dosage matches Rx",
      pass: Boolean(rx.dosage_match),
      note: rx.dosage_match
        ? undefined
        : `Requested “${rx.requested_order}” vs active ${rx.active_dosage}`,
    });
    out.push({
      label: "Recent visit (6mo)",
      pass: Boolean(rx.recent_visit),
      note: rx.last_visit ? `Last visit ${rx.last_visit}` : "No visit on file",
    });
    if (rx.conflict) {
      out.push({
        label: "No drug conflict",
        pass: false,
        note: rx.conflict_medication ? `Conflicts with ${rx.conflict_medication}` : undefined,
      });
    }
  }

  const sched = c.scheduling_eligibility as
    | {
        conflict?: boolean;
        conflict_reason?: string;
        consecutive_reschedule_count?: number;
        requires_manual_call?: boolean;
        alternative_slot_found?: boolean | null;
      }
    | undefined;
  if (sched) {
    out.push({
      label: "No calendar conflict",
      pass: !sched.conflict,
      note: sched.conflict ? sched.conflict_reason : undefined,
    });
    if (sched.alternative_slot_found != null) {
      out.push({ label: "Alternative slot found", pass: Boolean(sched.alternative_slot_found) });
    }
    out.push({
      label: "Within reschedule policy",
      pass: !sched.requires_manual_call,
      note: sched.requires_manual_call
        ? `${sched.consecutive_reschedule_count ?? "multiple"} consecutive reschedules`
        : undefined,
    });
  }

  const message = c.message as { adverse_reaction_reported?: boolean } | undefined;
  if (message) {
    out.push({
      label: "No adverse reaction",
      pass: !message.adverse_reaction_reported,
      note: message.adverse_reaction_reported ? "Patient reports a reaction" : undefined,
    });
  }

  return out;
}
