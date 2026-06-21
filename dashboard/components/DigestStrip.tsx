import {
  AlertOctagon,
  CalendarCheck,
  CheckCircle2,
  ClipboardList,
  HelpCircle,
  type LucideIcon,
} from "lucide-react";
import type { Task } from "@/lib/types";

interface DigestStripProps {
  tasks: Task[];
}

interface Kpi {
  key: string;
  label: string;
  value: number;
  Icon: LucideIcon;
  tone: string;
}

export default function DigestStrip({ tasks }: DigestStripProps) {
  // All counts derive from live task state, so they update on every action.
  const scheduledDone = tasks.filter(
    (t) => t.type === "schedule" && t.status === "done",
  ).length;
  const flagged = tasks.filter((t) => t.status === "escalated").length;
  const pending = tasks.filter(
    (t) => t.status === "ready" || t.status === "pending",
  ).length;
  const needInfo = tasks.filter((t) => t.status === "needs_info").length;
  const doneToday = tasks.filter((t) => t.status === "done").length;

  const kpis: Kpi[] = [
    {
      key: "scheduled",
      label: "Scheduled today",
      value: scheduledDone,
      Icon: CalendarCheck,
      tone: "text-primary",
    },
    {
      key: "pending",
      label: "Pending approval",
      value: pending,
      Icon: ClipboardList,
      tone: "text-navy",
    },
    {
      key: "needinfo",
      label: "Need info",
      value: needInfo,
      Icon: HelpCircle,
      tone: "text-accent",
    },
    {
      key: "flagged",
      label: "Escalations",
      value: flagged,
      Icon: AlertOctagon,
      tone: "text-destructive",
    },
    {
      key: "done",
      label: "Done today",
      value: doneToday,
      Icon: CheckCircle2,
      tone: "text-primary",
    },
  ];

  return (
    <section aria-label="Daily digest" className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      {kpis.map(({ key, label, value, Icon, tone }) => (
        <div
          key={key}
          className="rounded-[var(--radius)] border border-border bg-surface p-4"
        >
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-muted-foreground">
              {label}
            </span>
            <Icon className={`size-4 ${tone}`} aria-hidden="true" />
          </div>
          <p className="mt-2 text-3xl font-extrabold tabular-nums text-navy">
            {value}
          </p>
        </div>
      ))}
    </section>
  );
}
