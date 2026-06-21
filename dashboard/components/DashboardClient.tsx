"use client";

import { useMemo, useRef, useState } from "react";
import type { Task } from "@/lib/types";
import { bucketOf, sortForReview } from "@/lib/task";
import { useLiveTasks } from "@/lib/useLiveTasks";
import AppShell from "./AppShell";
import DigestStrip from "./DigestStrip";
import TaskSection from "./TaskSection";
import Toast from "./Toast";
import ResetDemoButton from "./ResetDemoButton";

const TODAY = new Date("2026-06-21").toLocaleDateString("en-US", {
  weekday: "long",
  month: "long",
  day: "numeric",
});

type Decision = "approve" | "reject" | "action_taken" | "mark_done";

interface ToastState {
  message: string;
  previous: Task | null; // snapshot for Undo
  tone: "success" | "error";
}

interface DashboardClientProps {
  initialTasks: Task[];
  /** True when the DB/env wasn't reachable and we're on local fixtures. */
  usingFixtures: boolean;
}

const NOW_ISO = "2026-06-21T09:00:00Z";

export default function DashboardClient({ initialTasks, usingFixtures }: DashboardClientProps) {
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [tasks, setTasks] = useLiveTasks(initialTasks, !usingFixtures && processingId === null);
  const [flashId, setFlashId] = useState<string | null>(null);
  const [toast, setToast] = useState<ToastState | null>(null);
  const flashTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const { toReview, followUp, done } = useMemo(() => {
    const groups = { toReview: [] as Task[], followUp: [] as Task[], done: [] as Task[] };
    for (const t of tasks) {
      const b = bucketOf(t);
      if (b === "to_review") groups.toReview.push(t);
      else if (b === "follow_up") groups.followUp.push(t);
      else groups.done.push(t);
    }
    return { toReview: sortForReview(groups.toReview), followUp: groups.followUp, done: groups.done };
  }, [tasks]);

  function flash(id: string) {
    setFlashId(id);
    if (flashTimer.current) clearTimeout(flashTimer.current);
    flashTimer.current = setTimeout(() => setFlashId(null), 900);
  }

  function replaceTask(id: string, next: Task) {
    setTasks((prev) => prev.map((t) => (t.id === id ? next : t)));
  }

  // Optimistically apply `optimistic`, then persist the decision via the API.
  // On fixtures (no DB) we skip the network and keep the local state. On error
  // we revert and surface it. The decision→DB-column mapping lives server-side.
  async function applyDecision(
    task: Task,
    decision: Decision,
    note: string,
    optimistic: Partial<Task>,
    message: string,
  ) {
    setProcessingId(task.id);
    const snapshot = task;
    replaceTask(task.id, { ...task, ...optimistic });

    if (usingFixtures) {
      setTimeout(() => {
        setProcessingId(null);
        setToast({ message, previous: snapshot, tone: "success" });
        flash(task.id);
      }, 350);
      return;
    }

    try {
      const res = await fetch(`/api/tasks/${task.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ decision, note }),
      });
      if (!res.ok) {
        const { error } = (await res.json().catch(() => ({}))) as { error?: string };
        throw new Error(error ?? `Request failed (${res.status})`);
      }
      const { task: updated, notice } = (await res.json()) as { task: Task; notice?: string };
      replaceTask(task.id, updated);
      setToast({ message: notice ? `${message} · ${notice}` : message, previous: snapshot, tone: "success" });
      flash(task.id);
    } catch (err) {
      replaceTask(task.id, snapshot); // revert
      const detail = err instanceof Error ? err.message : "Unknown error";
      setToast({ message: `Couldn't save — ${detail}`, previous: null, tone: "error" });
    } finally {
      setProcessingId(null);
    }
  }

  function handleApprove(task: Task, note: string) {
    applyDecision(
      task,
      "approve",
      note,
      { status: "complete", approved_at: NOW_ISO, reviewed_at: NOW_ISO, chw_note: note || null },
      `Approved — ${task.patient_name}`,
    );
  }

  function handleReject(task: Task, note: string) {
    applyDecision(
      task,
      "reject",
      note,
      { status: "rejected", rejected_at: NOW_ISO, reviewed_at: NOW_ISO, chw_note: note || null },
      `Rejected — ${task.patient_name} moved to follow-up`,
    );
  }

  function handleActionTaken(task: Task, note: string) {
    applyDecision(
      task,
      "action_taken",
      note,
      { status: "complete", approved_at: NOW_ISO, reviewed_at: NOW_ISO, chw_note: note || null },
      `Marked handled — ${task.patient_name}`,
    );
  }

  function handleMarkDone(task: Task) {
    applyDecision(
      task,
      "mark_done",
      "",
      { status: "complete", approved_at: NOW_ISO },
      `Closed out — ${task.patient_name}`,
    );
  }

  function handleUndo() {
    if (!toast?.previous) return;
    const prev = toast.previous;
    replaceTask(prev.id, prev);
    // On a live DB, undo also re-opens the task server-side (restores its prior
    // review status and clears the decision audit fields).
    if (!usingFixtures) {
      setProcessingId(prev.id);
      void fetch(`/api/tasks/${prev.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ decision: "reopen", status: prev.status }),
      })
        .catch(() => {})
        .finally(() => setProcessingId(null));
    }
    setToast(null);
  }

  return (
    <AppShell
      chwName="Riya Shah"
      active="queue"
      pendingCount={toReview.length}
      usingFixtures={usingFixtures}
      title="Work queue"
      subtitle={`${toReview.length} ${toReview.length === 1 ? "patient" : "patients"} awaiting review`}
      headerAside={
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center rounded-full border border-border bg-surface-muted px-3 py-1 text-xs font-semibold text-muted-foreground">
            {TODAY}
          </span>
          {!usingFixtures && <ResetDemoButton />}
        </div>
      }
    >
      <DigestStrip tasks={tasks} />

      <div className="mt-6 space-y-4">
          <TaskSection
            bucket="to_review"
            tasks={toReview}
            processingId={processingId}
            flashId={flashId}
            onApprove={handleApprove}
            onReject={handleReject}
            onActionTaken={handleActionTaken}
            onMarkDone={handleMarkDone}
          />
          <TaskSection
            bucket="follow_up"
            tasks={followUp}
            processingId={processingId}
            flashId={flashId}
            onApprove={handleApprove}
            onReject={handleReject}
            onActionTaken={handleActionTaken}
            onMarkDone={handleMarkDone}
          />
          <TaskSection
            bucket="done"
            tasks={done}
            processingId={processingId}
            flashId={flashId}
            defaultOpen={false}
            onApprove={handleApprove}
            onReject={handleReject}
            onActionTaken={handleActionTaken}
            onMarkDone={handleMarkDone}
          />
      </div>

      {toast && (
        <Toast
          message={toast.message}
          tone={toast.tone}
          onUndo={toast.previous ? handleUndo : undefined}
          onDismiss={() => setToast(null)}
        />
      )}
    </AppShell>
  );
}
