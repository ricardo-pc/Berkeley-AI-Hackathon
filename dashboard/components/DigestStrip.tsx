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
  tone: string;
}

export default function DigestStrip({ tasks }: DigestStripProps) {
  // All counts derive from live task state, so they update on every decision.
  const toReview = tasks.filter((t) => bucketOf(t) === "to_review");
  const emergencies = toReview.filter(isEmergency).length;
  const iffy = toReview.filter(isIffy).length;
  const followUp = tasks.filter((t) => bucketOf(t) === "follow_up").length;
  const done = tasks.filter((t) => bucketOf(t) === "done").length;

  const kpis: Kpi[] = [
    { key: "review", label: "Awaiting review", value: toReview.length, Icon: ClipboardList, tone: "text-navy" },
    { key: "emergency", label: "Emergencies", value: emergencies, Icon: AlertOctagon, tone: "text-destructive" },
    { key: "iffy", label: "Needs judgment", value: iffy, Icon: AlertTriangle, tone: "text-accent" },
    { key: "followup", label: "Follow-up", value: followUp, Icon: RotateCcw, tone: "text-accent" },
    { key: "done", label: "Done today", value: done, Icon: CheckCircle2, tone: "text-primary" },
  ];

  return (
    <section aria-label="Daily digest" className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      {kpis.map(({ key, label, value, Icon, tone }) => (
        <div key={key} className="rounded-[var(--radius)] border border-border bg-surface p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-muted-foreground">{label}</span>
            <Icon className={`size-4 ${tone}`} aria-hidden="true" />
          </div>
          <p className="mt-2 text-3xl font-extrabold tabular-nums text-navy">{value}</p>
        </div>
      ))}
    </section>
  );
}
