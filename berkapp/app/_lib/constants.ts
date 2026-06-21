// Static UI option lists for the EHR forms. These are picklists the eClinicalWorks
// UI would offer — not patient data — so they stay client-safe constants rather
// than DB reads. (Open scheduling slots are illustrative for the demo; real
// availability lives on providers.availability in Supabase.)

export const pharmacies = [
  "Walgreens #4821 — 2300 Shattuck Ave, Berkeley",
  "CVS #1190 — 2020 Oxford St, Berkeley",
  "Rite Aid #5573 — 1500 Solano Ave, Albany",
  "Berkeley Bowl Pharmacy — 920 Heinz Ave",
  "Mail Order — Express Scripts",
];

export const visitTypes = [
  "Office Visit — Established (15 min)",
  "Follow-up (20 min)",
  "Telephone Visit (10 min)",
  "Annual Wellness Visit (40 min)",
  "Prescription Review (15 min)",
  "New Patient (40 min)",
];

export const openSlots: Record<string, string[]> = {
  "06/23/2026": ["8:00 AM", "8:20 AM", "11:40 AM", "2:00 PM"],
  "06/24/2026": ["9:00 AM", "9:20 AM", "1:20 PM", "3:40 PM", "4:00 PM"],
  "06/25/2026": ["8:40 AM", "10:00 AM", "10:20 AM"],
  "06/26/2026": ["11:00 AM", "11:20 AM", "2:40 PM", "3:00 PM"],
};
