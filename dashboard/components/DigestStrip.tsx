import {
  AlertOctagon,
  AlertTriangle,
  CheckCircle2,
  ClipboardList,
  RotateCcw,
  type LucideIcon,
} from "lucide-react";
import type { Task } from "@/lib/types";
import { bucketOf, isEmergency, isIffy } from "@/lib/task";

interface DigestStripProps {
  tasks: Task[];
}

interface Kpi {
  key: string;
  label: string;
  value: number;
  Icon: LucideIcon;
  /** Icon chip color classes. */
  chip: string;
}

export default function DigestStrip({ tasks }: DigestStripProps) {
  // All counts derive from live task state, so they update on every decision.
  const toReview = tasks.filter((t) => bucketOf(t) === "to_review");
  const emergencies = toReview.filter(isEmergency).length;
  const iffy = toReview.filter(isIffy).length;
  const followUp = tasks.filter((t) => bucketOf(t) === "follow_up").length;
  const done = tasks.filter((t) => bucketOf(t) === "done").length;

  const kpis: Kpi[] = [
    { key: "review", label: "Awaiting review", value: toReview.length, Icon: ClipboardList, chip: "bg-primary-soft text-primary" },
    { key: "emergency", label: "Emergencies", value: emergencies, Icon: AlertOctagon, chip: "bg-destructive-soft text-destructive" },
    { key: "iffy", label: "Needs judgment", value: iffy, Icon: AlertTriangle, chip: "bg-warning-soft text-accent" },
    { key: "followup", label: "Follow-up", value: followUp, Icon: RotateCcw, chip: "bg-warning-soft text-accent" },
    { key: "done", label: "Done today", value: done, Icon: CheckCircle2, chip: "bg-success-soft text-primary-deep" },
  ];

  return (
    <section aria-label="Daily digest" className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      {kpis.map(({ key, label, value, Icon, chip }) => (
        <div
          key={key}
          className="rounded-[var(--radius)] border border-border bg-surface p-4 shadow-card transition-shadow hover:shadow-pop"
        >
          <span className={`grid size-8 place-items-center rounded-[var(--radius-sm)] ${chip}`}>
            <Icon className="size-[18px]" aria-hidden="true" />
          </span>
          <p className="mt-3 text-3xl font-extrabold tabular-nums leading-none text-navy">{value}</p>
          <p className="mt-1.5 text-sm font-medium text-muted-foreground">{label}</p>
        </div>
      ))}
    </section>
  );
}
