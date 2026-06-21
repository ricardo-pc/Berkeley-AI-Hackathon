import Link from "next/link";
import { Inbox, History, Stethoscope, type LucideIcon } from "lucide-react";
import { initials, avatarColor } from "@/lib/avatar";

interface SidebarProps {
  chwName: string;
  active: "queue" | "history";
  pendingCount?: number;
}

const NAV: { key: "queue" | "history"; label: string; href: string; Icon: LucideIcon }[] = [
  { key: "queue", label: "Work queue", href: "/", Icon: Inbox },
  { key: "history", label: "History", href: "/history", Icon: History },
];

export default function Sidebar({ chwName, active, pendingCount }: SidebarProps) {
  return (
    <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col border-r border-border bg-surface px-3 py-4 lg:flex">
      {/* Brand */}
      <div className="flex items-center gap-2.5 px-2 pb-4">
        <span className="grid size-9 place-items-center rounded-[var(--radius-sm)] bg-primary text-on-primary shadow-card" aria-hidden="true">
          <Stethoscope className="size-5" />
        </span>
        <div className="leading-tight">
          <p className="text-sm font-extrabold tracking-tight text-navy">Triage Desk</p>
          <p className="text-xs text-muted-foreground">Front-desk console</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex flex-col gap-1" aria-label="Primary">
        {NAV.map(({ key, label, href, Icon }) => {
          const isActive = key === active;
          return (
            <Link
              key={key}
              href={href}
              aria-current={isActive ? "page" : undefined}
              className={`group flex items-center gap-3 rounded-[var(--radius-sm)] px-3 py-2 text-sm font-semibold transition-colors ${
                isActive
                  ? "bg-primary-soft text-primary-deep"
                  : "text-muted-foreground hover:bg-surface-muted hover:text-navy"
              }`}
            >
              <Icon className={`size-[18px] ${isActive ? "text-primary" : "text-muted-foreground group-hover:text-navy"}`} aria-hidden="true" />
              <span className="flex-1">{label}</span>
              {key === "queue" && pendingCount != null && pendingCount > 0 && (
                <span
                  className={`tabular-nums rounded-full px-2 py-0.5 text-xs font-bold ${
                    isActive ? "bg-primary text-on-primary" : "bg-border-strong/60 text-navy"
                  }`}
                >
                  {pendingCount}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* CHW profile pinned to the bottom */}
      <div className="mt-auto flex items-center gap-3 rounded-[var(--radius)] border border-border bg-surface-muted p-3">
        <span className={`grid size-9 shrink-0 place-items-center rounded-full text-sm font-bold ${avatarColor(chwName)}`} aria-hidden="true">
          {initials(chwName)}
        </span>
        <div className="min-w-0 leading-tight">
          <p className="truncate text-sm font-bold text-navy">{chwName}</p>
          <p className="text-xs text-muted-foreground">Community Health Worker</p>
        </div>
      </div>
    </aside>
  );
}
