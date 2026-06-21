"use client";

import { useMemo, useState } from "react";
import { ArrowDownUp, Search } from "lucide-react";
import type { Task, TaskType } from "@/lib/types";
import { TASK_TYPE_TAG } from "@/lib/types";
import { decisionLabel, decisionTime, isDecided, type DecisionTone } from "@/lib/task";
import { initials, avatarColor } from "@/lib/avatar";
import { useLiveTasks } from "@/lib/useLiveTasks";

interface HistoryTableProps {
  tasks: Task[];
  usingFixtures: boolean;
}

type DecisionFilter = "all" | "approve" | "reject" | "handle";
type SortKey = "time" | "patient" | "type" | "decision";

const DECISION_FILTERS: { key: DecisionFilter; label: string }[] = [
  { key: "all", label: "All decisions" },
  { key: "approve", label: "Approved" },
  { key: "reject", label: "Rejected" },
  { key: "handle", label: "Handled" },
];

const TYPE_FILTERS: { key: TaskType | "all"; label: string }[] = [
  { key: "all", label: "All types" },
  { key: "prescription_refill", label: "Refill" },
  { key: "reschedule", label: "Schedule" },
  { key: "message_relay", label: "Relay" },
  { key: "escalate", label: "Escalation" },
];

const TONE_BADGE: Record<DecisionTone, string> = {
  approve: "bg-success-soft text-primary-deep",
  reject: "bg-destructive-soft text-destructive",
  handle: "bg-[color:var(--color-navy)]/10 text-navy",
};

function fmt(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export default function HistoryTable({ tasks: initialTasks, usingFixtures }: HistoryTableProps) {
  const [tasks] = useLiveTasks(initialTasks, !usingFixtures);
  const [query, setQuery] = useState("");
  const [decision, setDecision] = useState<DecisionFilter>("all");
  const [type, setType] = useState<TaskType | "all">("all");
  const [sort, setSort] = useState<{ key: SortKey; dir: 1 | -1 }>({ key: "time", dir: -1 });

  const rows = useMemo(() => {
    const q = query.trim().toLowerCase();
    const filtered = tasks.filter((t) => {
      if (!isDecided(t)) return false;
      const d = decisionLabel(t);
      if (decision !== "all" && d.tone !== decision) return false;
      if (type !== "all" && t.task_type !== type) return false;
      if (q) {
        const hay = `${t.patient_name} ${t.agent_summary} ${t.chw_note ?? ""}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });

    return filtered.sort((a, b) => {
      const dir = sort.dir;
      switch (sort.key) {
        case "patient":
          return a.patient_name.localeCompare(b.patient_name) * dir;
        case "type":
          return a.task_type.localeCompare(b.task_type) * dir;
        case "decision":
          return decisionLabel(a).label.localeCompare(decisionLabel(b).label) * dir;
        default:
          return decisionTime(a).localeCompare(decisionTime(b)) * dir;
      }
    });
  }, [tasks, query, decision, type, sort]);

  function toggleSort(key: SortKey) {
    setSort((s) => (s.key === key ? { key, dir: (s.dir * -1) as 1 | -1 } : { key, dir: 1 }));
  }

  const selectClass =
    "rounded-[var(--radius-sm)] border border-border bg-surface px-2.5 py-1.5 text-sm font-medium focus:border-primary focus:outline-none";

  return (
    <div className="overflow-hidden rounded-[var(--radius)] border border-border bg-surface shadow-card">
      {/* Filter bar */}
      <div className="flex flex-wrap items-center gap-2 border-b border-border p-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search patient, summary, or note…"
            aria-label="Search history"
            className="w-full rounded-[var(--radius-sm)] border border-border bg-surface py-1.5 pl-8 pr-2.5 text-sm focus:border-primary focus:outline-none"
          />
        </div>
        <select aria-label="Filter by decision" value={decision} onChange={(e) => setDecision(e.target.value as DecisionFilter)} className={selectClass}>
          {DECISION_FILTERS.map((f) => (
            <option key={f.key} value={f.key}>{f.label}</option>
          ))}
        </select>
        <select aria-label="Filter by type" value={type} onChange={(e) => setType(e.target.value as TaskType | "all")} className={selectClass}>
          {TYPE_FILTERS.map((f) => (
            <option key={f.key} value={f.key}>{f.label}</option>
          ))}
        </select>
        <span className="tabular-nums px-1 text-xs font-semibold text-muted-foreground">
          {rows.length} {rows.length === 1 ? "entry" : "entries"}
        </span>
      </div>

      {/* Excel-style dense table */}
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead className="sticky top-0 z-10 bg-surface-muted text-left">
            <tr className="[&>th]:border-b [&>th]:border-border [&>th]:px-3 [&>th]:py-2 [&>th]:font-bold [&>th]:text-navy [&>th]:whitespace-nowrap">
              <SortHeader label="When" active={sort.key === "time"} dir={sort.dir} onClick={() => toggleSort("time")} />
              <SortHeader label="Patient" active={sort.key === "patient"} dir={sort.dir} onClick={() => toggleSort("patient")} />
              <SortHeader label="Type" active={sort.key === "type"} dir={sort.dir} onClick={() => toggleSort("type")} />
              <SortHeader label="Decision" active={sort.key === "decision"} dir={sort.dir} onClick={() => toggleSort("decision")} />
              <th>Summary</th>
              <th>Note</th>
              <th>By</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-3 py-10 text-center text-sm text-muted-foreground">
                  No matching history.
                </td>
              </tr>
            ) : (
              rows.map((t, i) => {
                const d = decisionLabel(t);
                return (
                  <tr
                    key={t.id}
                    className={`[&>td]:border-b [&>td]:border-border [&>td]:px-3 [&>td]:py-2 [&>td]:align-middle ${
                      i % 2 ? "bg-surface" : "bg-surface-muted/50"
                    } transition-colors hover:bg-primary-soft/40`}
                  >
                    <td className="tabular-nums whitespace-nowrap text-muted-foreground">{fmt(decisionTime(t))}</td>
                    <td className="whitespace-nowrap font-semibold text-navy">
                      <span className="flex items-center gap-2">
                        <span className={`grid size-7 shrink-0 place-items-center rounded-full text-[11px] font-bold ${avatarColor(t.patient_name)}`} aria-hidden="true">
                          {initials(t.patient_name)}
                        </span>
                        {t.patient_name}
                      </span>
                    </td>
                    <td className="whitespace-nowrap text-muted-foreground">{TASK_TYPE_TAG[t.task_type]}</td>
                    <td className="whitespace-nowrap">
                      <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-bold ${TONE_BADGE[d.tone]}`}>
                        {d.label}
                      </span>
                    </td>
                    <td className="max-w-[24rem] text-foreground">{t.agent_summary}</td>
                    <td className="max-w-[16rem] text-muted-foreground">{t.chw_note || "—"}</td>
                    <td className="whitespace-nowrap text-muted-foreground">{t.reviewed_at ? "Riya Shah" : "—"}</td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function SortHeader({
  label,
  active,
  dir,
  onClick,
}: {
  label: string;
  active: boolean;
  dir: 1 | -1;
  onClick: () => void;
}) {
  return (
    <th>
      <button
        type="button"
        onClick={onClick}
        className={`inline-flex cursor-pointer items-center gap-1 font-bold ${active ? "text-primary" : "text-navy hover:text-primary"}`}
      >
        {label}
        <ArrowDownUp className={`size-3 ${active ? "opacity-100" : "opacity-40"} ${active && dir === 1 ? "rotate-180" : ""}`} aria-hidden="true" />
      </button>
    </th>
  );
}
