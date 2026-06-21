import "server-only";

import { getPatientIdentity } from "./tasks-repo";
import type { Task } from "./types";

// Base URL of the backend FastAPI service that owns the executor + confirmation
// agents (e.g. http://localhost:8000). When unset, approvals still complete but
// nothing is executed/texted — surfaced to the CHW via the returned notice.
const BASE = process.env.BACKEND_API_URL?.replace(/\/$/, "");

export interface ExecResult {
  /** false = the executor call failed; the approval should not be recorded. */
  ok: boolean;
  /** true = we actually called an executor endpoint (vs. status-only fallback). */
  executed: boolean;
  /** Human line for the CHW toast (confirmation SMS status, etc.). */
  notice?: string;
  error?: string;
}

function confirmationNotice(confirmation: unknown): string {
  const c = confirmation as { sent?: boolean; reason?: string } | null | undefined;
  if (!c) return "Done.";
  return c.sent
    ? "Patient texted a confirmation."
    : `Patient not texted — ${c.reason ?? "no confirmation sent"}.`;
}

// Refill/reschedule → POST the matching executor endpoint. The endpoint does the
// real write (prescriptions/appointments), flips the task to complete, and
// chains the confirmation SMS. Relay/escalate have no executor yet → caller
// falls back to a status-only complete.
export async function executeApproval(task: Task): Promise<ExecResult> {
  const pa = task.proposed_action;

  if (!pa || (pa.type !== "prescription_refill" && pa.type !== "reschedule")) {
    return { ok: true, executed: false };
  }
  if (!BASE) {
    return { ok: true, executed: false, notice: "Marked complete (executor not configured)." };
  }
  if (!task.patient_id) {
    return { ok: false, executed: false, error: "Task has no patient_id to execute against." };
  }

  const who = await getPatientIdentity(task.patient_id);
  const [path, body] =
    pa.type === "prescription_refill"
      ? [
          "/api/prescriptions",
          {
            patient_id: task.patient_id,
            ...who,
            medication_name: pa.medication_name,
            dosage: pa.dosage,
            instructions: pa.instructions ?? "",
            provider_id: pa.provider_id ?? "",
            task_id: task.id,
          },
        ]
      : [
          "/api/appointments",
          {
            patient_id: task.patient_id,
            ...who,
            provider_id: pa.provider_id ?? "",
            start_time: pa.new_start,
            end_time: pa.new_end ?? pa.new_start,
            cancel_appointment_id: pa.cancel_appointment_id ?? null,
            visit_type: "follow_up",
            task_id: task.id,
          },
        ];

  try {
    const res = await fetch(`${BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = (await res.json().catch(() => ({}))) as {
      success?: boolean;
      message?: string;
      error?: string;
      confirmation?: unknown;
    };
    if (!res.ok || data.success === false) {
      return { ok: false, executed: false, error: data.message ?? data.error ?? `Executor failed (${res.status})` };
    }
    return { ok: true, executed: true, notice: confirmationNotice(data.confirmation) };
  } catch (err) {
    return { ok: false, executed: false, error: err instanceof Error ? err.message : "Executor unreachable" };
  }
}
