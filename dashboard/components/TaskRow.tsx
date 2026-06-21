"use client";

import { useState } from "react";
import {
  Check,
  ChevronDown,
  Loader2,
  Phone,
  X,
  AlertTriangle,
  PlayCircle,
  CheckCheck,
  type LucideIcon,
} from "lucide-react";
import type { Bucket, Task } from "@/lib/types";
import { TASK_TYPE_TAG } from "@/lib/types";
import {
  ageFromDob,
  decisionModeOf,
  describeProposedAction,
  isIffy,
  presentChecks,
} from "@/lib/task";
import { rowStatusMeta } from "@/lib/status";

interface TaskRowProps {
  task: Task;
  bucket: Bucket;
  processing: boolean;
  flash: boolean;
  onApprove: (task: Task, note: string) => void;
  onReject: (task: Task, note: string) => void;
  onActionTaken: (task: Task, note: string) => void;
  onMarkDone: (task: Task) => void;
}

const TYPE_TAG_STYLE: Record<string, string> = {
  prescription_refill: "bg-success-soft text-primary-deep",
  reschedule: "bg-[color:var(--color-navy)]/10 text-navy",
  message_relay: "bg-warning-soft text-accent",
  escalate: "bg-destructive-soft text-destructive",
};

export default function TaskRow({
  task,
  bucket,
  processing,
  flash,
  onApprove,
  onReject,
  onActionTaken,
  onMarkDone,
}: TaskRowProps) {
  const [expanded, setExpanded] = useState(false);
  const [note, setNote] = useState("");

  const meta = rowStatusMeta(task);
  const checks = presentChecks(task.agent_checks);
  const mode = decisionModeOf(task);
  const iffy = isIffy(task);
  const age = ageFromDob(task.patient_dob);
  const detailId = `detail-${task.id}`;
  const ActionIcon: LucideIcon = mode === "action_taken" ? CheckCheck : Check;

  // Two-click flow: in the review queue the row must be opened ("Review")
  // before approve/reject are revealed. Elsewhere the toggle is just details.
  const isReview = bucket === "to_review";
  const reviewLabel = isReview ? (expanded ? "Hide" : "Review") : expanded ? "Hide details" : "Details";

  return (
    <article
      className={`rounded-[var(--radius)] border border-border border-l-4 bg-surface ${meta.accent} ${
        flash ? "animate-flash" : ""
      } ${bucket === "done" ? "opacity-80" : ""}`}
    >
      <div className="flex flex-col gap-3 p-4 sm:flex-row sm:items-start">
        <span
          className={`inline-grid h-7 w-fit shrink-0 place-items-center rounded-[6px] px-2 text-xs font-bold uppercase tracking-wide ${TYPE_TAG_STYLE[task.task_type]}`}
        >
          {TASK_TYPE_TAG[task.task_type]}
        </span>

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
            <strong className="text-navy">{task.patient_name}</strong>
            {age != null && (
              <span className="text-xs text-muted-foreground tabular-nums">{age}y</span>
            )}
            <span
              className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-semibold ${meta.chip}`}
            >
              <meta.Icon className="size-3" aria-hidden="true" />
              {meta.label}
            </span>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">{task.agent_summary}</p>

          <ul className="mt-2 flex flex-wrap gap-1.5">
            {checks.map((c) => (
              <li
                key={c.label}
                className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs ${
                  c.pass ? "bg-success-soft text-primary-deep" : "bg-warning-soft text-accent"
                }`}
              >
                {c.pass ? "✓" : "⚠"} {c.label}
              </li>
            ))}
          </ul>
        </div>

        {/* Right rail: primary affordance per bucket */}
        <div className="flex shrink-0 items-center gap-2 sm:flex-col sm:items-end">
          {bucket === "follow_up" && (
            <button
              type="button"
              onClick={() => onMarkDone(task)}
              disabled={processing}
              className="inline-flex min-h-[40px] cursor-pointer items-center justify-center gap-1.5 rounded-[var(--radius)] bg-primary px-3 text-sm font-bold text-on-primary transition-colors duration-200 hover:bg-primary-deep disabled:cursor-wait disabled:opacity-70"
            >
              {processing ? <Loader2 className="size-4 animate-spin" /> : <CheckCheck className="size-4" />}
              Mark done
            </button>
          )}
          {bucket === "done" && (
            <span className="inline-flex items-center gap-1.5 rounded-[var(--radius)] bg-success-soft px-3 py-2 text-sm font-semibold text-primary-deep">
              <Check className="size-4" aria-hidden="true" /> Done
            </span>
          )}

          <button
            type="button"
            onClick={() => setExpanded((v) => !v)}
            aria-expanded={expanded}
            aria-controls={detailId}
            className={`inline-flex cursor-pointer items-center gap-1 rounded-[var(--radius)] px-3 py-2 text-xs font-bold transition-colors duration-200 ${
              isReview && !expanded
                ? "bg-navy text-white hover:opacity-90"
                : "text-muted-foreground hover:text-navy"
            }`}
          >
            {reviewLabel}
            <ChevronDown
              className={`size-4 transition-transform duration-200 ${expanded ? "rotate-180" : ""}`}
              aria-hidden="true"
            />
          </button>
        </div>
      </div>

      {expanded && (
        <div id={detailId} className="border-t border-border bg-surface-muted/40 px-4 py-4">
          {/* Proposed action — exactly what Approve will execute. */}
          <div
            className={`rounded-[var(--radius)] border p-3 ${
              mode === "action_taken"
                ? "border-destructive/30 bg-destructive-soft/60"
                : "border-primary/30 bg-success-soft/60"
            }`}
          >
            <h4 className="text-xs font-bold uppercase tracking-wide text-muted-foreground">
              {mode === "action_taken" ? "Action required" : "Proposed action"}
            </h4>
            <p className="mt-1 flex items-start gap-2 text-sm font-semibold text-foreground">
              <PlayCircle className="mt-0.5 size-4 shrink-0 text-primary" aria-hidden="true" />
              {describeProposedAction(task.proposed_action)}
            </p>
          </div>

          {iffy && (
            <p className="mt-3 flex items-start gap-2 rounded-[var(--radius)] bg-warning-soft px-3 py-2 text-sm text-accent">
              <AlertTriangle className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
              <span>
                Eligibility gate failed{task.flagged_reason ? ` — ${task.flagged_reason}` : ""}. Use
                your judgment; a note is recommended for the record.
              </span>
            </p>
          )}

          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wide text-muted-foreground">
                Voicemail transcript
              </h4>
              <p className="mt-1 rounded-[var(--radius)] border border-border bg-surface p-3 text-sm italic text-foreground">
                “{task.transcript ?? "—"}”
              </p>
              {task.patient_phone && (
                <a
                  href={`tel:${task.patient_phone.replace(/[^\d+]/g, "")}`}
                  className="mt-2 inline-flex items-center gap-1.5 text-xs font-semibold text-primary hover:text-primary-deep"
                >
                  <Phone className="size-3.5" aria-hidden="true" />
                  {task.patient_phone}
                </a>
              )}
            </div>

            <div>
              <h4 className="text-xs font-bold uppercase tracking-wide text-muted-foreground">
                Eligibility checks
              </h4>
              <ul className="mt-1 space-y-1">
                {checks.map((c) => (
                  <li key={c.label} className="flex items-start gap-2 text-sm">
                    <span className={c.pass ? "text-primary" : "text-accent"} aria-hidden="true">
                      {c.pass ? "✓" : "⚠"}
                    </span>
                    <span>
                      <span className="font-medium">{c.label}</span>
                      {c.note && <span className="text-muted-foreground"> — {c.note}</span>}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Decision controls (only in the review queue) */}
          {isReview && (
            <div className="mt-4 border-t border-border pt-4">
              <label htmlFor={`note-${task.id}`} className="text-xs font-bold uppercase tracking-wide text-muted-foreground">
                Note {iffy ? "(recommended)" : "(optional)"}
              </label>
              <textarea
                id={`note-${task.id}`}
                value={note}
                onChange={(e) => setNote(e.target.value)}
                rows={2}
                placeholder="Add context for the audit trail…"
                className="mt-1 w-full resize-y rounded-[var(--radius)] border border-border bg-surface p-2 text-sm focus:outline-none"
              />

              <div className="mt-3 flex flex-wrap gap-2">
                {mode === "approve_reject" ? (
                  <>
                    <button
                      type="button"
                      onClick={() => onApprove(task, note)}
                      disabled={processing}
                      className="inline-flex min-h-[40px] cursor-pointer items-center justify-center gap-1.5 rounded-[var(--radius)] bg-primary px-4 text-sm font-bold text-on-primary transition-colors duration-200 hover:bg-primary-deep disabled:cursor-wait disabled:opacity-70"
                    >
                      {processing ? <Loader2 className="size-4 animate-spin" /> : <Check className="size-4" />}
                      Approve
                    </button>
                    <button
                      type="button"
                      onClick={() => onReject(task, note)}
                      disabled={processing}
                      className="inline-flex min-h-[40px] cursor-pointer items-center justify-center gap-1.5 rounded-[var(--radius)] bg-destructive px-4 text-sm font-bold text-white transition-colors duration-200 hover:opacity-90 disabled:cursor-wait disabled:opacity-70"
                    >
                      <X className="size-4" /> Reject
                    </button>
                  </>
                ) : (
                  <button
                    type="button"
                    onClick={() => onActionTaken(task, note)}
                    disabled={processing}
                    className="inline-flex min-h-[40px] cursor-pointer items-center justify-center gap-1.5 rounded-[var(--radius)] bg-navy px-4 text-sm font-bold text-white transition-colors duration-200 hover:opacity-90 disabled:cursor-wait disabled:opacity-70"
                  >
                    {processing ? <Loader2 className="size-4 animate-spin" /> : <ActionIcon className="size-4" />}
                    Action taken
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Rejected: show the note that sent it to follow-up */}
          {bucket === "follow_up" && task.chw_note && (
            <p className="mt-4 border-t border-border pt-3 text-sm">
              <span className="font-semibold text-navy">Why rejected: </span>
              <span className="text-muted-foreground">{task.chw_note}</span>
            </p>
          )}
          {bucket === "done" && task.chw_note && (
            <p className="mt-4 border-t border-border pt-3 text-sm text-muted-foreground">
              <span className="font-semibold text-navy">Note: </span>
              {task.chw_note}
            </p>
          )}
        </div>
      )}
    </article>
  );
}
