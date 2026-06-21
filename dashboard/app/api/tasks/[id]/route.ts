import { NextResponse } from "next/server";
import { getTask, patchTask, type TaskDecisionPatch } from "@/lib/tasks-repo";
import { executeApproval } from "@/lib/executor";

// The single CHW identity for the demo (matches AppHeader). Stored in approved_by
// for audit; swap for real auth later.
const CHW = "Riya Shah";

type Decision = "approve" | "reject" | "action_taken" | "mark_done" | "reopen";
const DECISIONS = new Set<Decision>(["approve", "reject", "action_taken", "mark_done", "reopen"]);
// Statuses a task can be restored to by an undo (back into the review queue).
const REOPEN_STATUSES = new Set(["pending_approval", "escalated"]);

// Server is authoritative about what each decision writes to the DB, so the
// client only sends { decision, note } and can't desync the status lifecycle.
function patchFor(decision: Decision, note: string | null, now: string, status?: string): TaskDecisionPatch {
  switch (decision) {
    case "approve":
    case "action_taken":
      return { status: "complete", approved_at: now, approved_by: CHW, reviewed_at: now, chw_note: note };
    case "reject":
      return { status: "rejected", rejected_at: now, reviewed_at: now, chw_note: note };
    case "mark_done":
      return { status: "complete", approved_at: now, approved_by: CHW };
    case "reopen":
      return {
        status: REOPEN_STATUSES.has(status ?? "") ? status : "pending_approval",
        approved_at: null,
        approved_by: null,
        rejected_at: null,
        reviewed_at: null,
        chw_note: null,
      };
  }
}

// PATCH /api/tasks/[id] — apply a CHW decision. Body: { decision, note?, status? }.
// Response: { task, notice? } where notice is a CHW-facing line (e.g. SMS status).
export async function PATCH(req: Request, { params }: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await params;
    const body = (await req.json()) as { decision?: Decision; note?: string; status?: string };
    const decision = body.decision;
    if (!decision || !DECISIONS.has(decision)) {
      return NextResponse.json({ error: "Invalid or missing `decision`." }, { status: 400 });
    }
    const note = body.note?.trim() ? body.note.trim() : null;
    const now = new Date().toISOString();

    const task = await getTask(id);
    if (!task) return NextResponse.json({ error: "Task not found." }, { status: 404 });

    // Approve = run the real executor (refill/reschedule) → it does the write,
    // flips status to complete, and sends the patient confirmation SMS.
    if (decision === "approve") {
      // Double-execution guard: never re-run an already-completed task.
      if (task.status === "complete") {
        return NextResponse.json({ task, notice: "Already completed — no action taken." });
      }

      const exec = await executeApproval(task);
      if (!exec.ok) {
        return NextResponse.json({ error: exec.error ?? "Execution failed." }, { status: 502 });
      }

      if (exec.executed) {
        // Executor already set status + approved_at; best-effort audit fields.
        try {
          await patchTask(id, { approved_by: CHW, reviewed_at: now, chw_note: note });
        } catch (e) {
          console.error("[tasks] audit patch failed (columns may be missing):", e);
        }
      } else {
        // Relay / escalate-stub / executor-not-configured → status-only complete.
        await patchTask(id, patchFor("approve", note, now));
      }
      const updated = (await getTask(id)) ?? task;
      return NextResponse.json({ task: updated, notice: exec.notice });
    }

    const updated = await patchTask(id, patchFor(decision, note, now, body.status));
    return NextResponse.json({ task: updated });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
