"use client";

import { useState } from "react";
import {
  Check,
  ChevronDown,
  Loader2,
  Phone,
  Eye,
  ArrowUpRight,
  type LucideIcon,
} from "lucide-react";
import type { ActionKind, Task } from "@/lib/types";
import { REQUEST_TYPE_TAG } from "@/lib/types";
import { STATUS_META } from "@/lib/status";

interface TaskRowProps {
  task: Task;
  processing: boolean;
  flash: boolean;
  onAction: (task: Task) => void;
}

const ACTION_ICON: Record<ActionKind, LucideIcon> = {
  approve: Check,
  review: Eye,
  call: Phone,
  open: ArrowUpRight,
};

const ACTION_STYLE: Record<ActionKind, string> = {
  approve: "bg-primary text-on-primary hover:bg-primary-deep",
  review: "bg-navy text-white hover:opacity-90",
  call: "bg-accent text-white hover:opacity-90",
  open: "bg-destructive text-white hover:opacity-90",
};

export default function TaskRow({
  task,
  processing,
  flash,
  onAction,
}: TaskRowProps) {
  const [expanded, setExpanded] = useState(false);
  const meta = STATUS_META[task.status];
  const isDone = task.status === "done";
  const ActionIcon = ACTION_ICON[task.action.kind];
  const detailId = `detail-${task.id}`;

  return (
    <article
      className={`rounded-[var(--radius)] border border-border border-l-4 bg-surface ${meta.accent} ${
        flash ? "animate-flash" : ""
      } ${isDone ? "opacity-80" : ""}`}
    >
      <div className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center">
        {/* Type tag */}
        <span className="inline-grid h-7 w-fit place-items-center rounded-[6px] bg-success-soft px-2 text-xs font-bold uppercase tracking-wide text-primary-deep">
          {REQUEST_TYPE_TAG[task.type]}
        </span>

        {/* Patient + summary + chips */}
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
            <strong className="text-navy">{task.patient.name}</strong>
            <span className="text-xs text-muted-foreground tabular-nums">
              DOB {task.patient.dob}
            </span>
            <span
              className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-semibold ${meta.chip}`}
            >
              <meta.Icon className="size-3" aria-hidden="true" />
              {meta.label}
            </span>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">{task.summary}</p>

          {/* Eligibility chips */}
          <ul className="mt-2 flex flex-wrap gap-1.5">
            {task.checks.map((c) => (
              <li
                key={c.label}
                className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs ${
                  c.pass
                    ? "bg-success-soft text-primary-deep"
                    : "bg-warning-soft text-accent"
                }`}
              >
                {c.pass ? "✓" : "⚠"} {c.label}
              </li>
            ))}
          </ul>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 sm:flex-col sm:items-end">
          {isDone ? (
            <span className="inline-flex items-center gap-1.5 rounded-[var(--radius)] bg-success-soft px-3 py-2 text-sm font-semibold text-primary-deep">
              <Check className="size-4" aria-hidden="true" /> Done
            </span>
          ) : (
            <button
              type="button"
              onClick={() => onAction(task)}
              disabled={processing}
              className={`inline-flex min-h-[40px] cursor-pointer items-center justify-center gap-1.5 rounded-[var(--radius)] px-3 text-sm font-bold transition-colors duration-200 disabled:cursor-wait disabled:opacity-70 ${
                ACTION_STYLE[task.action.kind]
              }`}
            >
              {processing ? (
                <Loader2 className="size-4 animate-spin" aria-hidden="true" />
              ) : (
                <ActionIcon className="size-4" aria-hidden="true" />
              )}
              {processing ? "Working…" : task.action.label}
            </button>
          )}

          <button
            type="button"
            onClick={() => setExpanded((v) => !v)}
            aria-expanded={expanded}
            aria-controls={detailId}
            aria-label={expanded ? "Hide details" : "Show details"}
            className="inline-flex cursor-pointer items-center gap-1 rounded-[var(--radius)] px-2 py-1.5 text-xs font-semibold text-muted-foreground hover:text-navy"
          >
            Details
            <ChevronDown
              className={`size-4 transition-transform duration-200 ${
                expanded ? "rotate-180" : ""
              }`}
              aria-hidden="true"
            />
          </button>
        </div>
      </div>

      {/* Expanded detail */}
      {expanded && (
        <div
          id={detailId}
          className="border-t border-border bg-surface-muted/40 px-4 py-4"
        >
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wide text-muted-foreground">
                Voicemail transcript
              </h4>
              <p className="mt-1 rounded-[var(--radius)] border border-border bg-surface p-3 text-sm italic text-foreground">
                “{task.transcript}”
              </p>
              <p className="mt-2 text-xs text-muted-foreground tabular-nums">
                {task.patient.phone}
              </p>
            </div>

            <div>
              <h4 className="text-xs font-bold uppercase tracking-wide text-muted-foreground">
                Extracted details
              </h4>
              <dl className="mt-1 grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-sm">
                {Object.entries(task.details).map(([k, v]) => (
                  <div key={k} className="contents">
                    <dt className="text-muted-foreground">{k}</dt>
                    <dd className="font-medium text-foreground">{v}</dd>
                  </div>
                ))}
              </dl>

              <h4 className="mt-3 text-xs font-bold uppercase tracking-wide text-muted-foreground">
                Agent checklist
              </h4>
              <ul className="mt-1 space-y-1">
                {task.checks.map((c) => (
                  <li key={c.label} className="flex items-start gap-2 text-sm">
                    <span
                      className={c.pass ? "text-primary" : "text-accent"}
                      aria-hidden="true"
                    >
                      {c.pass ? "✓" : "⚠"}
                    </span>
                    <span>
                      <span className="font-medium">{c.label}</span>
                      {c.note && (
                        <span className="text-muted-foreground"> — {c.note}</span>
                      )}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </article>
  );
}
