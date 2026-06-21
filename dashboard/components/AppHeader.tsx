import Link from "next/link";
import { Voicemail } from "lucide-react";

interface AppHeaderProps {
  chwName: string;
  active: "queue" | "history";
  pendingCount?: number;
}

const TODAY = new Date("2026-06-21").toLocaleDateString("en-US", {
  weekday: "long",
  month: "long",
  day: "numeric",
});

const NAV = [
  { key: "queue", label: "Queue", href: "/" },
  { key: "history", label: "History", href: "/history" },
] as const;

export default function AppHeader({ chwName, active, pendingCount }: AppHeaderProps) {
  return (
    <header className="border-b border-teal-900 bg-gradient-to-b from-teal-700 to-teal-900 text-white">
      <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-3">
            <span className="grid size-9 place-items-center rounded-[var(--radius)] bg-primary" aria-hidden="true">
              <Voicemail className="size-5" />
            </span>
            <div>
              <h1 className="text-lg font-extrabold leading-tight">Voicemail Work Queue</h1>
              <p className="text-sm text-white/70">{TODAY}</p>
            </div>
          </div>

          <nav className="flex items-center gap-1 rounded-full bg-white/10 p-1" aria-label="Primary">
            {NAV.map((item) => {
              const isActive = item.key === active;
              return (
                <Link
                  key={item.key}
                  href={item.href}
                  aria-current={isActive ? "page" : undefined}
                  className={`flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-semibold transition-colors ${
                    isActive ? "bg-white text-navy" : "text-white/80 hover:text-white"
                  }`}
                >
                  {item.label}
                  {item.key === "queue" && pendingCount != null && pendingCount > 0 && (
                    <span
                      className={`tabular-nums rounded-full px-1.5 text-xs font-bold ${
                        isActive ? "bg-navy/10 text-navy" : "bg-white/20 text-white"
                      }`}
                    >
                      {pendingCount}
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="flex items-center gap-2 rounded-full bg-white/10 px-3 py-1.5 text-sm">
          <span className="size-2 rounded-full bg-primary" aria-hidden="true" />
          <span className="font-semibold">{chwName}</span>
          <span className="text-white/60">CHW</span>
        </div>
      </div>
    </header>
  );
}
