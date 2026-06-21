"use client";

import { useState } from "react";
import { ChevronDown, Inbox } from "lucide-react";
import type { Bucket, Task } from "@/lib/types";
import { BUCKET_META } from "@/lib/status";
import TaskRow from "./TaskRow";

interface TaskSectionProps {
  bucket: Bucket;
  tasks: Task[];
  processingId: string | null;
  flashId: string | null;
  defaultOpen?: boolean;
  onApprove: (task: Task, note: string) => void;
  onReject: (task: Task, note: string) => void;
  onActionTaken: (task: Task, note: string) => void;
  onMarkDone: (task: Task) => void;
}

export default function TaskSection({
  bucket,
  tasks,
  processingId,
  flashId,
  defaultOpen = true,
  onApprove,
  onReject,
  onActionTaken,
  onMarkDone,
}: TaskSectionProps) {
  const [open, setOpen] = useState(defaultOpen);
  const meta = BUCKET_META[bucket];
  const sectionId = `bucket-${bucket}`;
  const danger = bucket === "follow_up";

  return (
    <section className="rounded-[var(--radius)] border border-border bg-surface shadow-card">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-controls={sectionId}
        className={`flex w-full cursor-pointer items-center justify-between gap-2 rounded-t-[var(--radius)] px-4 py-3 text-left transition-colors hover:bg-surface-muted ${
          open ? "border-b border-border" : "rounded-b-[var(--radius)]"
        }`}
      >
        <span className="flex items-center gap-2.5">
          <span
            className={`grid size-7 place-items-center rounded-[var(--radius-sm)] ${
              danger ? "bg-warning-soft text-accent" : "bg-surface-muted text-muted-foreground"
            }`}
          >
            <meta.Icon className="size-4" aria-hidden="true" />
          </span>
          <h2 className="text-sm font-bold text-navy">{meta.title}</h2>
          <span
            className={`tabular-nums rounded-full px-2 py-0.5 text-xs font-bold ${
              danger ? "bg-warning-soft text-accent" : "bg-surface-muted text-muted-foreground"
            }`}
          >
            {tasks.length}
          </span>
        </span>
        <ChevronDown
          className={`size-5 text-muted-foreground transition-transform duration-200 ${open ? "rotate-180" : ""}`}
          aria-hidden="true"
        />
      </button>

      {open && (
        <div id={sectionId} className="space-y-2.5 p-3">
          <p className="px-1 pb-0.5 text-xs text-muted-foreground">{meta.blurb}</p>
          {tasks.length === 0 ? (
            <div className="flex flex-col items-center gap-1 rounded-[var(--radius)] border border-dashed border-border py-8 text-center">
              <Inbox className="size-5 text-muted-foreground" aria-hidden="true" />
              <p className="text-sm text-muted-foreground">{meta.emptyText}</p>
            </div>
          ) : (
            tasks.map((task) => (
              <TaskRow
                key={task.id}
                task={task}
                bucket={bucket}
                processing={processingId === task.id}
                flash={flashId === task.id}
                onApprove={onApprove}
                onReject={onReject}
                onActionTaken={onActionTaken}
                onMarkDone={onMarkDone}
              />
            ))
          )}
        </div>
      )}
    </section>
  );
}
