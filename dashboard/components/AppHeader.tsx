import { Voicemail } from "lucide-react";

interface AppHeaderProps {
  chwName: string;
  pendingCount: number;
}

const TODAY = new Date("2026-06-20").toLocaleDateString("en-US", {
  weekday: "long",
  month: "long",
  day: "numeric",
});

export default function AppHeader({ chwName, pendingCount }: AppHeaderProps) {
  return (
    <header className="border-b border-border bg-navy text-white">
      <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <div className="flex items-center gap-3">
          <span
            className="grid size-9 place-items-center rounded-[var(--radius)] bg-primary"
            aria-hidden="true"
          >
            <Voicemail className="size-5" />
          </span>
          <div>
            <h1 className="text-lg font-extrabold leading-tight">
              Voicemail Work Queue
            </h1>
            <p className="text-sm text-white/70">{TODAY}</p>
          </div>
        </div>

        <div className="flex items-center gap-4 text-sm">
          <p className="text-white/80">
            <span className="font-semibold text-white tabular-nums">
              {pendingCount}
            </span>{" "}
            task{pendingCount === 1 ? "" : "s"} awaiting you
          </p>
          <div className="flex items-center gap-2 rounded-full bg-white/10 px-3 py-1.5">
            <span
              className="size-2 rounded-full bg-primary"
              aria-hidden="true"
            />
            <span className="font-semibold">{chwName}</span>
            <span className="text-white/60">CHW</span>
          </div>
        </div>
      </div>
    </header>
  );
}
