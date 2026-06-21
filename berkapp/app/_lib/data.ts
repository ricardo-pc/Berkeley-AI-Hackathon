// Mock EHR data for the eClinicalWorks-style demo.
// This is the "host system" our plugin would sit inside. Everything here is
// static seed data for now — later this gets swapped for Supabase. Keep the
// shape (Patient + the lookups below) stable so the swap is a data-source change,
// not a UI change.

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
  highAlert?: boolean; // narrow-therapeutic / severe-interaction drugs
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

export type Patient = {
  id: string;
  mrn: string;
  name: string;
  preferredName?: string;
  dob: string;
  age: number;
  sex: string;
  phone: string;
  language: string;
  pcp: string;
  insurance: string;
  insuranceId: string;
  balance: string;
  address: string;
  photoInitials: string;
  flag?: string; // short status surfaced in the patient list
  lastVisit: string;
  allergies: Allergy[];
  problems: Problem[];
  medications: Medication[];
  inrHistory: InrReading[]; // empty unless on anticoagulation
  appointments: Appointment[];
};

export const patients: Patient[] = [
  {
    id: "chen",
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
    flag: "Coumadin — INR overdue",
    lastVisit: "05/22/2026",
    allergies: [
      { substance: "Penicillin", reaction: "Hives", severity: "Moderate" },
      { substance: "Sulfa drugs", reaction: "Rash", severity: "Mild" },
    ],
    problems: [
      { code: "I48.91", description: "Atrial fibrillation, unspecified", since: "2019" },
      { code: "I10", description: "Essential hypertension", since: "2011" },
      { code: "E11.9", description: "Type 2 diabetes mellitus", since: "2015" },
      { code: "E78.5", description: "Hyperlipidemia, unspecified", since: "2014" },
    ],
    medications: [
      {
        id: "chen-warfarin",
        name: "Warfarin (Coumadin)",
        dose: "5 mg tablet",
        sig: "Take as directed per INR results",
        qty: "30 tablets",
        refillsLeft: 0,
        lastFilled: "05/22/2026",
        prescriber: "Dr. A. Okafor, MD",
        pharmacy: "Walgreens #4821 — Berkeley",
        status: "Active",
        highAlert: true,
      },
      {
        id: "chen-lisinopril",
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
        id: "chen-metformin",
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
        id: "chen-atorvastatin",
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
    ],
    inrHistory: [
      { date: "05/22/2026", inr: 2.4, dose: "35 mg/wk", action: "Continue current dose" },
      { date: "05/08/2026", inr: 2.1, dose: "35 mg/wk", action: "Continue current dose" },
      { date: "04/24/2026", inr: 1.8, dose: "32.5 mg/wk", action: "Increase dose" },
      { date: "04/10/2026", inr: 3.6, dose: "35 mg/wk", action: "Hold 1 day, decrease dose" },
      { date: "03/27/2026", inr: 2.6, dose: "37.5 mg/wk", action: "Decrease dose" },
    ],
    appointments: [
      {
        id: "chen-appt-1",
        date: "07/15/2026",
        time: "10:30 AM",
        provider: "Dr. A. Okafor, MD",
        type: "Follow-up — Anticoagulation",
        status: "Scheduled",
      },
    ],
  },
  {
    id: "okeefe",
    mrn: "MRN-0102874",
    name: "Daniel J. O'Keefe",
    preferredName: "Dan",
    dob: "09/02/1968",
    age: 57,
    sex: "Male",
    phone: "(510) 555-0143",
    language: "English",
    pcp: "Dr. P. Singh, DO",
    insurance: "Blue Shield PPO",
    insuranceId: "BSC-77120-09",
    balance: "$40.00",
    address: "512 Carlton St, Berkeley, CA 94704",
    photoInitials: "DO",
    flag: "Refill request — voicemail",
    lastVisit: "03/11/2026",
    allergies: [],
    problems: [
      { code: "I10", description: "Essential hypertension", since: "2016" },
      { code: "E78.5", description: "Hyperlipidemia, unspecified", since: "2018" },
    ],
    medications: [
      {
        id: "okeefe-lisinopril",
        name: "Lisinopril",
        dose: "10 mg tablet",
        sig: "Take 1 tablet by mouth daily",
        qty: "90 tablets",
        refillsLeft: 1,
        lastFilled: "04/14/2026",
        prescriber: "Dr. P. Singh, DO",
        pharmacy: "CVS #1190 — Berkeley",
        status: "Active",
      },
      {
        id: "okeefe-rosuvastatin",
        name: "Rosuvastatin",
        dose: "10 mg tablet",
        sig: "Take 1 tablet by mouth at bedtime",
        qty: "90 tablets",
        refillsLeft: 3,
        lastFilled: "04/14/2026",
        prescriber: "Dr. P. Singh, DO",
        pharmacy: "CVS #1190 — Berkeley",
        status: "Active",
      },
    ],
    inrHistory: [],
    appointments: [],
  },
  {
    id: "patterson",
    mrn: "MRN-0094550",
    name: "Gloria Patterson",
    dob: "11/27/1958",
    age: 67,
    sex: "Female",
    phone: "(510) 555-0199",
    language: "English",
    pcp: "Dr. A. Okafor, MD",
    insurance: "Medicare Advantage (Kaiser)",
    insuranceId: "MA-55120-KP",
    balance: "$0.00",
    address: "98 Ashby Ave, Berkeley, CA 94703",
    photoInitials: "GP",
    flag: "Refill due — no visit in 14 mo",
    lastVisit: "04/19/2025",
    allergies: [{ substance: "Codeine", reaction: "Nausea", severity: "Mild" }],
    problems: [
      { code: "E11.9", description: "Type 2 diabetes mellitus", since: "2013" },
      { code: "E66.9", description: "Obesity, unspecified", since: "2013" },
    ],
    medications: [
      {
        id: "patterson-metformin",
        name: "Metformin",
        dose: "500 mg tablet",
        sig: "Take 1 tablet by mouth twice daily",
        qty: "180 tablets",
        refillsLeft: 0,
        lastFilled: "10/22/2025",
        prescriber: "Dr. A. Okafor, MD",
        pharmacy: "Rite Aid #5573 — Albany",
        status: "Active",
      },
    ],
    inrHistory: [],
    appointments: [],
  },
  {
    id: "nguyen",
    mrn: "MRN-0110233",
    name: "Linh Nguyen",
    dob: "06/30/1991",
    age: 34,
    sex: "Female",
    phone: "(510) 555-0177",
    language: "English / Vietnamese",
    pcp: "Dr. P. Singh, DO",
    insurance: "Anthem HMO",
    insuranceId: "ANT-33891-CA",
    balance: "$15.00",
    address: "1402 University Ave, Berkeley, CA 94702",
    photoInitials: "LN",
    flag: "Reschedule request — voicemail",
    lastVisit: "05/30/2026",
    allergies: [],
    problems: [{ code: "J45.909", description: "Asthma, unspecified, uncomplicated", since: "2008" }],
    medications: [
      {
        id: "nguyen-albuterol",
        name: "Albuterol HFA",
        dose: "90 mcg inhaler",
        sig: "2 puffs every 4-6 hours as needed",
        qty: "1 inhaler",
        refillsLeft: 2,
        lastFilled: "05/30/2026",
        prescriber: "Dr. P. Singh, DO",
        pharmacy: "Walgreens #4821 — Berkeley",
        status: "Active",
      },
    ],
    inrHistory: [],
    appointments: [
      {
        id: "nguyen-appt-1",
        date: "06/27/2026",
        time: "3:20 PM",
        provider: "Dr. P. Singh, DO",
        type: "Office Visit — Established",
        status: "Scheduled",
      },
    ],
  },
  {
    id: "harris",
    mrn: "MRN-0107741",
    name: "Marcus Harris",
    dob: "01/19/1981",
    age: 45,
    sex: "Male",
    phone: "(510) 555-0166",
    language: "English",
    pcp: "Dr. L. Reyes, MD",
    insurance: "United Healthcare PPO",
    insuranceId: "UHC-90211-X",
    balance: "$0.00",
    address: "2210 Dwight Way, Berkeley, CA 94704",
    photoInitials: "MH",
    flag: "Message for provider — voicemail",
    lastVisit: "06/02/2026",
    allergies: [],
    problems: [{ code: "E78.5", description: "Hyperlipidemia, unspecified", since: "2022" }],
    medications: [
      {
        id: "harris-atorvastatin",
        name: "Atorvastatin",
        dose: "20 mg tablet",
        sig: "Take 1 tablet by mouth at bedtime",
        qty: "90 tablets",
        refillsLeft: 2,
        lastFilled: "06/02/2026",
        prescriber: "Dr. L. Reyes, MD",
        pharmacy: "Berkeley Bowl Pharmacy",
        status: "Active",
      },
    ],
    inrHistory: [],
    appointments: [],
  },
];

export function getPatient(id: string): Patient | undefined {
  return patients.find((p) => p.id === id);
}

// ---- Practice-level lookups (shared across patients) ----

export const providers: Provider[] = [
  { id: "okafor", name: "Dr. A. Okafor, MD", specialty: "Internal Medicine" },
  { id: "reyes", name: "Dr. L. Reyes, MD", specialty: "Cardiology" },
  { id: "singh", name: "Dr. P. Singh, DO", specialty: "Internal Medicine" },
  { id: "nurse", name: "J. Whitfield, RN", specialty: "Anticoagulation Clinic" },
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
