"use client";

// Dark top "badge bar" (brand + patient search + workflow counters). Shared by
// the scheduler and encounters screens. Counters are illustrative chrome.
const BADGES: [string, number, string][] = [
  ["P", 0, "bg-slate-500"], ["N", 2, "bg-amber-400 text-slate-900"],
  ["E", 0, "bg-teal-500"], ["S", 0, "bg-emerald-500"], ["D", 53, "bg-sky-500"],
  ["R", 24, "bg-yellow-500 text-slate-900"], ["T", 29, "bg-orange-500"],
  ["L", 3, "bg-cyan-500"], ["M", 1472, "bg-rose-500"],
];

export function BadgeBar() {
  return (
    <header className="flex flex-shrink-0 items-center gap-3 bg-gradient-to-b from-teal-700 to-teal-900 px-3 py-1.5 text-white">
      <button className="rounded p-1 text-lg leading-none hover:bg-white/15" aria-label="Menu">☰</button>
      <span className="flex h-7 w-7 items-center justify-center rounded-full bg-white text-sm font-bold text-teal-700">e</span>
      <span className="text-sm font-semibold tracking-tight">
        eGyulical<span className="text-teal-300">Works</span> 11e
      </span>
      <div className="ml-2 flex items-center gap-1 rounded bg-white/15 px-2 py-1 text-[11px]">
        <span aria-hidden>🔍</span>
        <input
          placeholder="Patient name / DOB / Acct No."
          className="w-44 bg-transparent placeholder-white/60 focus:outline-none"
        />
      </div>
      <div className="ml-auto flex items-center gap-1.5">
        {BADGES.map(([letter, count, color]) => (
          <span key={letter} className="flex items-center gap-1" title={`${letter}: ${count}`}>
            <span className="text-[10px] text-white/80">{letter}</span>
            <span className={`flex min-w-[20px] items-center justify-center rounded-full px-1.5 py-0.5 text-[10px] font-bold ${color}`}>
              {count}
            </span>
          </span>
        ))}
      </div>
    </header>
  );
}
