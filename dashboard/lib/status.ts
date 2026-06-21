import {
  AlertOctagon,
  AlertTriangle,
  CheckCircle2,
  Clock,
  type LucideIcon,
} from "lucide-react";
import type { TaskStatus } from "./types";

export interface StatusMeta {
  label: string;
  Icon: LucideIcon;
  /** Tailwind classes for the status chip (text + bg + border). */
  chip: string;
  /** Left accent border color class for the row. */
  accent: string;
}

// Status meaning is conveyed by icon + text + color together (never color alone),
// per ui-ux-pro-max `color-not-only`.
export const STATUS_META: Record<TaskStatus, StatusMeta> = {
  ready: {
    label: "Ready to approve",
    Icon: CheckCircle2,
    chip: "text-primary-deep bg-success-soft border-primary/30",
    accent: "border-l-primary",
  },
  needs_info: {
    label: "Needs info",
    Icon: AlertTriangle,
    chip: "text-accent bg-warning-soft border-accent/30",
    accent: "border-l-accent",
  },
  pending: {
    label: "Awaiting call",
    Icon: Clock,
    chip: "text-accent bg-warning-soft border-accent/30",
    accent: "border-l-accent",
  },
  escalated: {
    label: "Escalated",
    Icon: AlertOctagon,
    chip: "text-destructive bg-destructive-soft border-destructive/30",
    accent: "border-l-destructive",
  },
  done: {
    label: "Done",
    Icon: CheckCircle2,
    chip: "text-muted-foreground bg-surface-muted border-border",
    accent: "border-l-border",
  },
};
