// Mock EHR data for the eClinicalWorks-style demo.
// This is the "host system" our plugin would sit inside. Everything here is
// static seed data — no backend. The point of these screens is to show how
// many manual steps the front-desk path takes today.

export type Medication = {
  id: string;
  name: string;
  dose: string;
  sig: string; // directions
  qty: string;
  refillsLeft: number;
  lastFilled: string;
  prescriber: string;
  pharmacy: string;
  status: "Active" | "Discontinued";
  controlled?: boolean;
};

export type Allergy = { substance: string; reaction: string; severity: string };

export type Problem = { code: string; description: string; since: string };

export type InrReading = {
  date: string;
  inr: number;
  dose: string; // weekly dose at the time
  action: string;
};

export type Provider = { id: string; name: string; specialty: string };

export type Appointment = {
  id: string;
  date: string;
  time: string;
  provider: string;
  type: string;
  status: "Scheduled" | "Confirmed" | "Cancelled";
};

export const patient = {
  mrn: "MRN-0098213",
  name: "Margaret R. Chen",
  preferredName: "Maggie",
  dob: "03/14/1953",
  age: 73,
  sex: "Female",
  phone: "(510) 555-0182",
  language: "English",
  pcp: "Dr. A. Okafor, MD",
  insurance: "Medicare Part B + AARP Supplement",
  insuranceId: "1EG4-TE5-MK72",
  balance: "$0.00",
  address: "1847 Shattuck Ave, Berkeley, CA 94709",
  photoInitials: "MC",
};

export const allergies: Allergy[] = [
  { substance: "Penicillin", reaction: "Hives", severity: "Moderate" },
  { substance: "Sulfa drugs", reaction: "Rash", severity: "Mild" },
];

export const problems: Problem[] = [
  { code: "I48.91", description: "Atrial fibrillation, unspecified", since: "2019" },
  { code: "I10", description: "Essential hypertension", since: "2011" },
  { code: "E11.9", description: "Type 2 diabetes mellitus", since: "2015" },
  { code: "E78.5", description: "Hyperlipidemia, unspecified", since: "2014" },
];

export const medications: Medication[] = [
  {
    id: "rx-warfarin",
    name: "Warfarin (Coumadin)",
    dose: "5 mg tablet",
    sig: "Take as directed per INR results",
    qty: "30 tablets",
    refillsLeft: 0,
    lastFilled: "05/22/2026",
    prescriber: "Dr. A. Okafor, MD",
    pharmacy: "Walgreens #4821 — Berkeley",
    status: "Active",
  },
  {
    id: "rx-lisinopril",
    name: "Lisinopril",
    dose: "20 mg tablet",
    sig: "Take 1 tablet by mouth daily",
    qty: "90 tablets",
    refillsLeft: 2,
    lastFilled: "04/30/2026",
    prescriber: "Dr. A. Okafor, MD",
    pharmacy: "Walgreens #4821 — Berkeley",
    status: "Active",
  },
  {
    id: "rx-metformin",
    name: "Metformin",
    dose: "1000 mg tablet",
    sig: "Take 1 tablet by mouth twice daily with meals",
    qty: "180 tablets",
    refillsLeft: 1,
    lastFilled: "05/02/2026",
    prescriber: "Dr. A. Okafor, MD",
    pharmacy: "Walgreens #4821 — Berkeley",
    status: "Active",
  },
  {
    id: "rx-atorvastatin",
    name: "Atorvastatin",
    dose: "40 mg tablet",
    sig: "Take 1 tablet by mouth at bedtime",
    qty: "90 tablets",
    refillsLeft: 0,
    lastFilled: "03/18/2026",
    prescriber: "Dr. A. Okafor, MD",
    pharmacy: "Walgreens #4821 — Berkeley",
    status: "Active",
  },
];

export const inrHistory: InrReading[] = [
  { date: "05/22/2026", inr: 2.4, dose: "35 mg/wk", action: "Continue current dose" },
  { date: "05/08/2026", inr: 2.1, dose: "35 mg/wk", action: "Continue current dose" },
  { date: "04/24/2026", inr: 1.8, dose: "32.5 mg/wk", action: "Increase dose" },
  { date: "04/10/2026", inr: 3.6, dose: "35 mg/wk", action: "Hold 1 day, decrease dose" },
  { date: "03/27/2026", inr: 2.6, dose: "37.5 mg/wk", action: "Decrease dose" },
];

export const providers: Provider[] = [
  { id: "okafor", name: "Dr. A. Okafor, MD", specialty: "Internal Medicine" },
  { id: "reyes", name: "Dr. L. Reyes, MD", specialty: "Cardiology" },
  { id: "singh", name: "Dr. P. Singh, DO", specialty: "Internal Medicine" },
  { id: "nurse", name: "J. Whitfield, RN", specialty: "Anticoagulation Clinic" },
];

export const upcomingAppointments: Appointment[] = [
  {
    id: "appt-1",
    date: "07/15/2026",
    time: "10:30 AM",
    provider: "Dr. A. Okafor, MD",
    type: "Follow-up — Anticoagulation",
    status: "Scheduled",
  },
];

// Open appointment slots for the (very manual) scheduling screen.
export const openSlots: Record<string, string[]> = {
  "06/23/2026": ["8:00 AM", "8:20 AM", "11:40 AM", "2:00 PM"],
  "06/24/2026": ["9:00 AM", "9:20 AM", "1:20 PM", "3:40 PM", "4:00 PM"],
  "06/25/2026": ["8:40 AM", "10:00 AM", "10:20 AM"],
  "06/26/2026": ["11:00 AM", "11:20 AM", "2:40 PM", "3:00 PM"],
};

export const pharmacies = [
  "Walgreens #4821 — 2300 Shattuck Ave, Berkeley",
  "CVS #1190 — 2020 Oxford St, Berkeley",
  "Rite Aid #5573 — 1500 Solano Ave, Albany",
  "Berkeley Bowl Pharmacy — 920 Heinz Ave",
  "Mail Order — Express Scripts",
];

export const visitTypes = [
  "Office Visit — Established (15 min)",
  "Follow-up — Anticoagulation (20 min)",
  "Telephone Visit (10 min)",
  "Annual Wellness Visit (40 min)",
  "Lab Only — INR draw (5 min)",
];
