"use client";

import { useState } from "react";
import { ChevronDown, Inbox } from "lucide-react";
import type { RequestType, Task } from "@/lib/types";
import { REQUEST_TYPE_LABEL } from "@/lib/types";
import TaskRow from "./TaskRow";

interface TaskGroupProps {
  type: RequestType;
  tasks: Task[];
  processingId: string | null;
  flashId: string | null;
  onAction: (task: Task) => void;
}

export default function TaskGroup({
  type,
  tasks,
  processingId,
  flashId,
  onAction,
}: TaskGroupProps) {
  const [open, setOpen] = useState(true);
  const isEscalation = type === "escalation";
  const sectionId = `group-${type}`;

  return (
    <section
      className={`rounded-[var(--radius)] border bg-surface ${
        isEscalation ? "border-destructive/40" : "border-border"
      }`}
    >
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-controls={sectionId}
        className="flex w-full cursor-pointer items-center justify-between gap-2 rounded-t-[var(--radius)] px-4 py-3 text-left"
      >
        <span className="flex items-center gap-2">
          <h2
            className={`text-sm font-extrabold uppercase tracking-wide ${
              isEscalation ? "text-destructive" : "text-navy"
            }`}
          >
            {REQUEST_TYPE_LABEL[type]}
          </h2>
          <span
            className={`tabular-nums rounded-full px-2 py-0.5 text-xs font-bold ${
              isEscalation
                ? "bg-destructive-soft text-destructive"
                : "bg-surface-muted text-muted-foreground"
            }`}
          >
            {tasks.length}
          </span>
        </span>
        <ChevronDown
          className={`size-5 text-muted-foreground transition-transform duration-200 ${
            open ? "rotate-180" : ""
          }`}
          aria-hidden="true"
        />
      </button>

      {open && (
        <div id={sectionId} className="space-y-2 px-3 pb-3">
          {tasks.length === 0 ? (
            <div className="flex flex-col items-center gap-1 rounded-[var(--radius)] border border-dashed border-border py-8 text-center">
              <Inbox className="size-5 text-muted-foreground" aria-hidden="true" />
              <p className="text-sm text-muted-foreground">
                Nothing here — you&rsquo;re caught up.
              </p>
            </div>
          ) : (
            tasks.map((task) => (
              <TaskRow
                key={task.id}
                task={task}
                processing={processingId === task.id}
                flash={flashId === task.id}
                onAction={onAction}
              />
            ))
          )}
        </div>
      )}
    </section>
  );
}
