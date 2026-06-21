// EHR-facing types. These are the shapes the UI renders, mapped from Supabase
// rows in ehr.ts. Kept in a client-safe module (no server-only import) so client
// components can import the types without pulling in the DB client.

export type Allergy = { substance: string; reaction: string; severity: string };
export type Problem = { code: string; description: string; since: string };
export type InrReading = { date: string; inr: number; dose: string; action: string };

export type Provider = { id: string; name: string; specialty: string };

export type Medication = {
  id: string;
  name: string;
  dose: string;
  sig: string;
  qty?: string;
  refillsLeft: number | null; // null = not tracked in source data
  lastFilled: string;
  prescriber: string;
  pharmacy?: string;
  status: "Active" | "Discontinued";
  highAlert?: boolean;
};

export type Appointment = {
  id: string;
  date: string;
  time: string;
  startISO: string;
  provider: string;
  type: string;
  status: string;
};

export type Patient = {
  id: string;
  mrn: string;
  name: string;
  firstName: string;
  lastName: string;
  dob: string;
  age: number;
  sex?: string;
  phone: string;
  language?: string;
  pcp: string;
  insurance: string;
  insuranceId: string;
  insuranceValid: boolean;
  balance?: string;
  address?: string;
  photoInitials: string;
  lastVisit: string;
  // Sections without a backing Supabase table yet — rendered as empty states.
  allergies: Allergy[];
  problems: Problem[];
  inrHistory: InrReading[];
  medications: Medication[];
  appointments: Appointment[];
};

export type PatientSummary = {
  id: string;
  name: string;
  dob: string;
  age: number;
  sex?: string;
  mrn: string;
  pcp: string;
  phone: string;
  lastVisit: string;
  flag?: string;
  photoInitials: string;
};

export type PatientBundle = {
  patient: Patient;
  providers: Provider[];
};
