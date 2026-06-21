"use client";

// eClinicalWorks-style far-left module rail. Shared by the scheduler and the
// EHR frame so the left taskbar is consistent across screens.
const RAIL: [string, string][] = [
  ["⭐", "Favorites"], ["☰", "Menu"], ["🏥", "Practice"], ["📊", "PHM"],
  ["📒", "Registry"], ["↗", "Referrals"], ["✉", "Messages"], ["📄", "Documents"],
  ["💲", "Billing"], ["📈", "Analytics"], ["🌿", "healow"], ["⚙", "Admin"],
  ["🩺", "OccHealth"], ["🎥", "EVC"],
];

export function IconRail() {
  return (
    <nav className="flex w-14 flex-shrink-0 flex-col items-center overflow-y-auto bg-gradient-to-b from-sky-700 to-sky-900 py-1 text-white">
      {RAIL.map(([icon, label]) => (
        <button
          key={label}
          className="flex w-full flex-col items-center gap-0.5 py-1.5 text-center hover:bg-white/10"
          title={label}
        >
          <span className="text-base leading-none" aria-hidden>{icon}</span>
          <span className="text-[8px] leading-tight">{label}</span>
        </button>
      ))}
    </nav>
  );
}
