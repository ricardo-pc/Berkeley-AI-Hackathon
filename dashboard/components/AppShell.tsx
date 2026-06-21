import Link from "next/link";
import { Inbox, History, Stethoscope } from "lucide-react";
import Sidebar from "./Sidebar";

interface AppShellProps {
  chwName: string;
  active: "queue" | "history";
  pendingCount?: number;
  usingFixtures?: boolean;
  title: string;
  subtitle?: string;
  /** Optional element rendered on the right of the page header (e.g. date). */
  headerAside?: React.ReactNode;
  children: React.ReactNode;
}

export default function AppShell({
  chwName,
  active,
  pendingCount,
  usingFixtures,
  title,
  subtitle,
  headerAside,
  children,
}: AppShellProps) {
  return (
    <div className="flex min-h-screen">
      <Sidebar chwName={chwName} active={active} pendingCount={pendingCount} />

      <div className="flex min-w-0 flex-1 flex-col">
        {/* Mobile top bar (sidebar is hidden < lg) */}
        <div className="flex items-center justify-between border-b border-border bg-surface px-4 py-3 lg:hidden">
          <div className="flex items-center gap-2">
            <span className="grid size-8 place-items-center rounded-[var(--radius-sm)] bg-primary text-on-primary" aria-hidden="true">
              <Stethoscope className="size-4" />
            </span>
            <span className="text-sm font-extrabold text-navy">Triage Desk</span>
          </div>
          <nav className="flex items-center gap-1" aria-label="Primary">
            <Link
              href="/"
              aria-current={active === "queue" ? "page" : undefined}
              className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-bold ${active === "queue" ? "bg-primary-soft text-primary-deep" : "text-muted-foreground"}`}
            >
              <Inbox className="size-4" /> Queue
            </Link>
            <Link
              href="/history"
              aria-current={active === "history" ? "page" : undefined}
              className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-bold ${active === "history" ? "bg-primary-soft text-primary-deep" : "text-muted-foreground"}`}
            >
              <History className="size-4" /> History
            </Link>
          </nav>
        </div>

        {usingFixtures && (
          <div className="border-b border-amber-200 bg-warning-soft px-4 py-1.5 text-center text-xs font-semibold text-accent">
            Demo data — not connected to the live database
          </div>
        )}

        {/* Page header */}
        <header className="border-b border-border bg-surface px-4 py-5 sm:px-8">
          <div className="mx-auto flex max-w-6xl flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h1 className="text-xl font-extrabold tracking-tight text-navy sm:text-2xl">{title}</h1>
              {subtitle && <p className="mt-0.5 text-sm text-muted-foreground">{subtitle}</p>}
            </div>
            {headerAside}
          </div>
        </header>

        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 sm:px-8">{children}</main>
      </div>
    </div>
  );
}
