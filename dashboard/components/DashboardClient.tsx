"use client";

import { useMemo, useRef, useState } from "react";
import type { Task, TaskStatus } from "@/lib/types";
import { REQUEST_TYPE_ORDER } from "@/lib/types";
import { SEED_TASKS } from "@/lib/mockData";
import AppHeader from "./AppHeader";
import DigestStrip from "./DigestStrip";
import StatusTabs, { type TabKey } from "./StatusTabs";
import TaskGroup from "./TaskGroup";
import Toast from "./Toast";

const PENDING_STATUSES: TaskStatus[] = [
  "ready",
  "needs_info",
  "pending",
  "escalated",
];

interface ToastState {
  message: string;
  previous: Task | null; // snapshot for Undo
}

export default function DashboardClient() {
  const [tasks, setTasks] = useState<Task[]>(SEED_TASKS);
  const [tab, setTab] = useState<TabKey>("all");
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [flashId, setFlashId] = useState<string | null>(null);
  const [toast, setToast] = useState<ToastState | null>(null);
  const flashTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const counts: Record<TabKey, number> = useMemo(
    () => ({
      all: tasks.length,
      pending: tasks.filter((t) => t.status !== "done").length,
      done: tasks.filter((t) => t.status === "done").length,
    }),
    [tasks],
  );

  const visible = useMemo(() => {
    if (tab === "pending") return tasks.filter((t) => t.status !== "done");
    if (tab === "done") return tasks.filter((t) => t.status === "done");
    return tasks;
  }, [tasks, tab]);

  function updateStatus(id: string, status: TaskStatus) {
    setTasks((prev) => prev.map((t) => (t.id === id ? { ...t, status } : t)));
  }

  function handleAction(task: Task) {
    // Only "approve" auto-completes. Review/call/open mark the task as awaiting a
    // human and never silently execute clinical work.
    if (task.action.kind !== "approve") {
      const label =
        task.action.kind === "open" || task.action.kind === "call"
          ? "pending"
          : "needs_info";
      // Surface that the row now needs a person; keep it out of "Done".
      updateStatus(task.id, label as TaskStatus);
      setToast({
        message:
          task.action.kind === "open"
            ? `Escalation opened for ${task.patient.name} — call now`
            : `Flagged ${task.patient.name} for a human follow-up`,
        previous: null,
      });
      return;
    }

    // Simulate the action agent executing (>300ms → show spinner per UX rules).
    setProcessingId(task.id);
    setTimeout(() => {
      setProcessingId(null);
      updateStatus(task.id, "done");
      setToast({ message: `Approved: ${task.summary}`, previous: task });

      // brief success flash on the row
      setFlashId(task.id);
      if (flashTimer.current) clearTimeout(flashTimer.current);
      flashTimer.current = setTimeout(() => setFlashId(null), 900);
    }, 600);
  }

  function handleUndo() {
    if (!toast?.previous) return;
    const prev = toast.previous;
    setTasks((cur) => cur.map((t) => (t.id === prev.id ? prev : t)));
    setToast(null);
  }

  const pendingCount = counts.pending;

  return (
    <div className="flex min-h-full flex-col">
      <AppHeader chwName="Riya Shah" pendingCount={pendingCount} />

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 sm:px-6">
        <DigestStrip tasks={tasks} />

        <div className="mt-6 flex items-center justify-between">
          <h2 className="text-base font-bold text-navy">Request lanes</h2>
          <StatusTabs active={tab} counts={counts} onChange={setTab} />
        </div>

        <div className="mt-4 space-y-4">
          {REQUEST_TYPE_ORDER.map((type) => (
            <TaskGroup
              key={type}
              type={type}
              tasks={visible.filter((t) => t.type === type)}
              processingId={processingId}
              flashId={flashId}
              onAction={handleAction}
            />
          ))}
        </div>
      </main>

      {toast && (
        <Toast
          message={toast.message}
          onUndo={toast.previous ? handleUndo : undefined}
          onDismiss={() => setToast(null)}
        />
      )}
    </div>
  );
}
