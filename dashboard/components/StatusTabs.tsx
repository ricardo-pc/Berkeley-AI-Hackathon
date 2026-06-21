"use client";

export type TabKey = "all" | "pending" | "done";

interface StatusTabsProps {
  active: TabKey;
  counts: Record<TabKey, number>;
  onChange: (tab: TabKey) => void;
}

const TABS: { key: TabKey; label: string }[] = [
  { key: "all", label: "All" },
  { key: "pending", label: "Pending" },
  { key: "done", label: "Done" },
];

export default function StatusTabs({ active, counts, onChange }: StatusTabsProps) {
  return (
    <div
      role="tablist"
      aria-label="Filter tasks by status"
      className="inline-flex rounded-[var(--radius)] border border-border bg-surface p-1"
    >
      {TABS.map(({ key, label }) => {
        const isActive = key === active;
        return (
          <button
            key={key}
            role="tab"
            type="button"
            aria-selected={isActive}
            onClick={() => onChange(key)}
            className={`flex cursor-pointer items-center gap-2 rounded-[6px] px-4 py-2 text-sm font-semibold transition-colors duration-200 ${
              isActive
                ? "bg-navy text-white"
                : "text-muted-foreground hover:text-navy"
            }`}
          >
            {label}
            <span
              className={`tabular-nums rounded-full px-1.5 py-0.5 text-xs font-bold ${
                isActive ? "bg-white/20 text-white" : "bg-surface-muted text-muted-foreground"
              }`}
            >
              {counts[key]}
            </span>
          </button>
        );
      })}
    </div>
  );
}
