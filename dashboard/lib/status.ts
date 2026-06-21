import {
  AlertOctagon,
  AlertTriangle,
  CheckCircle2,
  Clock,
  RotateCcw,
  type LucideIcon,
} from "lucide-react";
import type { Bucket, Task, TaskStatus } from "./types";
import { isEmergency, isIffy } from "./task";

export interface StatusMeta {
  label: string;
  Icon: LucideIcon;
  /** Tailwind classes for the status chip (text + bg + border). */
  chip: string;
  /** Left accent border color class for the row. */
  accent: string;
}

// Status meaning is conveyed by icon + text + color together (never color alone),
// per ui-ux-pro-max `color-not-only`. We derive a per-row descriptor from the
// task because a `escalated` row means different things for actionable
// (iffy — needs judgment) vs non-actionable (manual handling / emergency) items.
export function rowStatusMeta(task: Task): StatusMeta {
  if (isEmergency(task)) {
    return {
      label: "Emergency",
      Icon: AlertOctagon,
      chip: "text-destructive bg-destructive-soft border-destructive/30",
      accent: "border-l-destructive",
    };
  }
  if (isIffy(task)) {
    return {
      label: "Needs judgment",
      Icon: AlertTriangle,
      chip: "text-accent bg-warning-soft border-accent/30",
      accent: "border-l-accent",
    };
  }
  return STATUS_META[task.status];
}

export const STATUS_META: Record<TaskStatus, StatusMeta> = {
  pending_approval: {
    label: "Ready to approve",
    Icon: CheckCircle2,
    chip: "text-primary-deep bg-success-soft border-primary/30",
    accent: "border-l-primary",
  },
  escalated: {
    label: "Manual handling",
    Icon: AlertOctagon,
    chip: "text-destructive bg-destructive-soft border-destructive/30",
    accent: "border-l-destructive",
  },
  rejected: {
    label: "Rejected — follow up",
    Icon: RotateCcw,
    chip: "text-accent bg-warning-soft border-accent/30",
    accent: "border-l-accent",
  },
  complete: {
    label: "Done",
    Icon: CheckCircle2,
    chip: "text-muted-foreground bg-surface-muted border-border",
    accent: "border-l-border",
  },
};

export interface BucketMeta {
  title: string;
  Icon: LucideIcon;
  blurb: string;
  emptyText: string;
}

export const BUCKET_META: Record<Bucket, BucketMeta> = {
  to_review: {
    title: "To review",
    Icon: Clock,
    blurb: "Most urgent first — review, then approve or reject.",
    emptyText: "Inbox zero — nothing awaiting review.",
  },
  follow_up: {
    title: "Rejected — needs follow-up",
    Icon: RotateCcw,
    blurb: "Rejected tasks you still need to call or message about, then mark done.",
    emptyText: "No follow-ups outstanding.",
  },
  done: {
    title: "Done today",
    Icon: CheckCircle2,
    blurb: "Approved or handled.",
    emptyText: "Nothing completed yet.",
  },
};
