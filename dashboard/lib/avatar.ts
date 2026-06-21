// Person avatars give the queue a CRM "managing people" feel. We derive both
// the initials and a stable color from the name so the same patient always
// looks the same across the queue, history, and detail views.

/** Up to two initials from a name ("Susan Park" → "SP", "Cher" → "CH"). */
export function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

// Soft bg / readable text pairs (standard Tailwind palette). Kept off the
// status hues (sky/amber/rose) so avatars never read as a status signal.
const PALETTE = [
  "bg-violet-100 text-violet-700",
  "bg-emerald-100 text-emerald-700",
  "bg-indigo-100 text-indigo-700",
  "bg-cyan-100 text-cyan-700",
  "bg-fuchsia-100 text-fuchsia-700",
  "bg-teal-100 text-teal-700",
  "bg-blue-100 text-blue-700",
  "bg-lime-100 text-lime-700",
];

/** Deterministic avatar color classes for a name. */
export function avatarColor(name: string): string {
  let hash = 0;
  for (let i = 0; i < name.length; i++) hash = (hash * 31 + name.charCodeAt(i)) | 0;
  return PALETTE[Math.abs(hash) % PALETTE.length];
}
