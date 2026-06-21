import "server-only";

import { supabaseAdmin } from "./supabase";
import type {
  Appointment,
  Medication,
  Patient,
  PatientBundle,
  PatientSummary,
  Provider,
} from "./types";

// ---- DB row shapes (what Supabase returns) ----

type PatientRow = {
  id: string;
  first_name: string;
  last_name: string;
  date_of_birth: string; // YYYY-MM-DD
  phone: string | null;
  insurance_plan: string | null;
  insurance_id: string | null;
  insurance_valid: boolean | null;
  preferred_provider_id: string | null;
};

type ProviderRow = { id: string; name: string; specialty: string | null };

type PrescriptionRow = {
  id: string;
  patient_id: string;
  provider_id: string | null;
  medication_name: string;
  dosage: string | null;
  instructions: string | null;
  prescribed_at: string | null;
  active: boolean | null;
};

type AppointmentRow = {
  id: string;
  patient_id: string;
  provider_id: string | null;
  start_time: string;
  end_time: string | null;
  visit_type: string | null;
  status: string | null;
};

type TaskRow = {
  patient_id: string | null;
  task_type: string | null;
  status: string | null;
  created_at: string | null;
};

// "today" for the demo. Matches the seeded data's frame of reference.
const NOW = new Date("2026-06-20T12:00:00Z");

// Medications we treat as high-alert / narrow-therapeutic-index for the
// interaction-warning step. Matched case-insensitively on name.
const HIGH_ALERT = ["warfarin", "coumadin", "insulin", "digoxin", "heparin"];

// ---- formatting helpers ----

function fmtDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return "—";
  const mm = String(d.getUTCMonth() + 1).padStart(2, "0");
  const dd = String(d.getUTCDate()).padStart(2, "0");
  return `${mm}/${dd}/${d.getUTCFullYear()}`;
}

function fmtTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return "—";
  let h = d.getUTCHours();
  const m = String(d.getUTCMinutes()).padStart(2, "0");
  const ampm = h >= 12 ? "PM" : "AM";
  h = h % 12 || 12;
  return `${h}:${m} ${ampm}`;
}

function ageFrom(dob: string): number {
  const d = new Date(dob);
  let age = NOW.getUTCFullYear() - d.getUTCFullYear();
  const m = NOW.getUTCMonth() - d.getUTCMonth();
  if (m < 0 || (m === 0 && NOW.getUTCDate() < d.getUTCDate())) age--;
  return age;
}

function initials(first: string, last: string): string {
  return `${first?.[0] ?? ""}${last?.[0] ?? ""}`.toUpperCase();
}

function mrnFrom(id: string): string {
  // uuids are like a1b2c3d4-0001-0001-... — surface the readable middle block.
  const block = id.split("-")[1] ?? id.slice(0, 6);
  return `MRN-${block}`;
}

function prettyVisitType(v: string | null | undefined): string {
  if (!v) return "Office Visit";
  return v
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

function cap(s: string | null | undefined): string {
  if (!s) return "—";
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function taskFlag(t: TaskRow): string {
  const type =
    t.task_type === "prescription_refill"
      ? "Refill"
      : t.task_type === "reschedule"
        ? "Reschedule"
        : t.task_type === "message_relay"
          ? "Message"
          : cap(t.task_type);
  const status =
    t.status === "pending_approval"
      ? "pending approval"
      : t.status === "escalated"
        ? "escalated"
        : t.status ?? "";
  return `${type} — ${status}`;
}

// ---- mappers ----

function mapMedication(r: PrescriptionRow, providerName: string): Medication {
  return {
    id: r.id,
    name: r.medication_name,
    dose: r.dosage ?? "—",
    sig: r.instructions ?? "—",
    refillsLeft: null, // not tracked in the prescriptions table
    lastFilled: fmtDate(r.prescribed_at),
    prescriber: providerName,
    status: r.active === false ? "Discontinued" : "Active",
    highAlert: HIGH_ALERT.some((h) =>
      r.medication_name.toLowerCase().includes(h),
    ),
  };
}

function mapAppointment(r: AppointmentRow, providerName: string): Appointment {
  return {
    id: r.id,
    date: fmtDate(r.start_time),
    time: fmtTime(r.start_time),
    startISO: r.start_time,
    provider: providerName,
    type: prettyVisitType(r.visit_type),
    status: cap(r.status),
  };
}

// ---- queries ----

export async function getProviders(): Promise<Provider[]> {
  const { data } = await supabaseAdmin()
    .from("providers")
    .select("id,name,specialty");
  return (data ?? []).map((p: ProviderRow) => ({
    id: p.id,
    name: p.name,
    specialty: p.specialty ?? "—",
  }));
}

export async function getPatients(): Promise<PatientSummary[]> {
  const db = supabaseAdmin();
  const [patientsRes, providersRes, apptsRes, tasksRes] = await Promise.all([
    db.from("patients").select("*"),
    db.from("providers").select("id,name"),
    db.from("appointments").select("patient_id,start_time,status"),
    db.from("tasks").select("patient_id,task_type,status,created_at"),
  ]);

  const providerName = new Map<string, string>(
    (providersRes.data ?? []).map((p: { id: string; name: string }) => [
      p.id,
      p.name,
    ]),
  );

  // last past appointment per patient
  const lastVisit = new Map<string, string>();
  for (const a of (apptsRes.data ?? []) as AppointmentRow[]) {
    if (new Date(a.start_time) > NOW) continue;
    const cur = lastVisit.get(a.patient_id);
    if (!cur || new Date(a.start_time) > new Date(cur)) {
      lastVisit.set(a.patient_id, a.start_time);
    }
  }

  // most-recent open task per patient → list flag
  const openTask = new Map<string, TaskRow>();
  for (const t of (tasksRes.data ?? []) as TaskRow[]) {
    if (!t.patient_id) continue;
    if (t.status === "approved") continue;
    const cur = openTask.get(t.patient_id);
    if (
      !cur ||
      new Date(t.created_at ?? 0) > new Date(cur.created_at ?? 0)
    ) {
      openTask.set(t.patient_id, t);
    }
  }

  return ((patientsRes.data ?? []) as PatientRow[])
    .map((p) => ({
      id: p.id,
      name: `${p.first_name} ${p.last_name}`,
      dob: fmtDate(p.date_of_birth),
      age: ageFrom(p.date_of_birth),
      mrn: mrnFrom(p.id),
      pcp: p.preferred_provider_id
        ? (providerName.get(p.preferred_provider_id) ?? "—")
        : "—",
      phone: p.phone ?? "—",
      lastVisit: fmtDate(lastVisit.get(p.id)),
      flag: openTask.has(p.id) ? taskFlag(openTask.get(p.id)!) : undefined,
      photoInitials: initials(p.first_name, p.last_name),
    }))
    .sort((a, b) => a.name.localeCompare(b.name));
}

// ---- scheduler (day view) ----

const WEEKDAY_KEYS = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"] as const;

function hhmmToMinutes(value: string | null | undefined): number | null {
  if (!value) return null;
  const m = /^(\d{1,2}):(\d{2})/.exec(value);
  if (!m) return null;
  return Number(m[1]) * 60 + Number(m[2]);
}

function utcMinutes(iso: string): number {
  const d = new Date(iso);
  return d.getUTCHours() * 60 + d.getUTCMinutes();
}

export type ScheduleProvider = {
  id: string;
  name: string;
  specialty: string;
  // Working window for the selected weekday, as minutes from midnight (UTC).
  availStartMin: number | null;
  availEndMin: number | null;
};

export type ScheduleAppointment = {
  id: string;
  providerId: string | null;
  patientId: string;
  patientName: string; // "Last, First"
  patientDob: string; // MM/DD/YYYY
  patientPhone: string;
  startISO: string;
  startMinutes: number;
  endMinutes: number;
  visitType: string;
  status: string;
};

export type DaySchedule = {
  providers: ScheduleProvider[];
  appointments: ScheduleAppointment[];
};

// Pulls every appointment on a given calendar day (YYYY-MM-DD, UTC) and shapes
// it for the eClinicalWorks-style column-per-provider grid.
export async function getDaySchedule(dateISO: string): Promise<DaySchedule> {
  const db = supabaseAdmin();

  const dayStart = `${dateISO}T00:00:00Z`;
  const next = new Date(dayStart);
  next.setUTCDate(next.getUTCDate() + 1);
  const dayEnd = next.toISOString();
  const weekday = WEEKDAY_KEYS[new Date(dayStart).getUTCDay()];

  const [provRes, apptRes] = await Promise.all([
    db.from("providers").select("id,name,specialty,availability").order("name"),
    db
      .from("appointments")
      .select("*")
      .gte("start_time", dayStart)
      .lt("start_time", dayEnd)
      .order("start_time"),
  ]);

  type ProviderAvailRow = ProviderRow & {
    availability: Record<string, [string, string]> | null;
  };

  const providers: ScheduleProvider[] = ((provRes.data ?? []) as ProviderAvailRow[]).map(
    (p) => {
      const window = p.availability?.[weekday] ?? null;
      return {
        id: p.id,
        name: p.name,
        specialty: p.specialty ?? "—",
        availStartMin: window ? hhmmToMinutes(window[0]) : null,
        availEndMin: window ? hhmmToMinutes(window[1]) : null,
      };
    },
  );

  const appts = (apptRes.data ?? []) as AppointmentRow[];
  const patientIds = [...new Set(appts.map((a) => a.patient_id))];

  const patientsById = new Map<string, PatientRow>();
  if (patientIds.length) {
    const { data } = await db
      .from("patients")
      .select("id,first_name,last_name,date_of_birth,phone")
      .in("id", patientIds);
    for (const p of (data ?? []) as PatientRow[]) patientsById.set(p.id, p);
  }

  const appointments: ScheduleAppointment[] = appts.map((a) => {
    const p = patientsById.get(a.patient_id);
    const startMinutes = utcMinutes(a.start_time);
    const endMinutes = a.end_time ? utcMinutes(a.end_time) : startMinutes + 30;
    return {
      id: a.id,
      providerId: a.provider_id,
      patientId: a.patient_id,
      patientName: p ? `${p.last_name}, ${p.first_name}` : "Unknown patient",
      patientDob: fmtDate(p?.date_of_birth),
      patientPhone: p?.phone ?? "—",
      startISO: a.start_time,
      startMinutes,
      endMinutes: Math.max(endMinutes, startMinutes + 15),
      visitType: prettyVisitType(a.visit_type),
      status: a.status ?? "scheduled",
    };
  });

  return { providers, appointments };
}

export async function getPatientBundle(id: string): Promise<PatientBundle | null> {
  const db = supabaseAdmin();

  const { data: pRows } = await db
    .from("patients")
    .select("*")
    .eq("id", id)
    .limit(1);
  const p = (pRows ?? [])[0] as PatientRow | undefined;
  if (!p) return null;

  const [providersRes, rxRes, apptsRes] = await Promise.all([
    db.from("providers").select("id,name,specialty"),
    db.from("prescriptions").select("*").eq("patient_id", id),
    db.from("appointments").select("*").eq("patient_id", id),
  ]);

  const providers: Provider[] = (providersRes.data ?? []).map((r: ProviderRow) => ({
    id: r.id,
    name: r.name,
    specialty: r.specialty ?? "—",
  }));
  const providerName = new Map(providers.map((r) => [r.id, r.name]));

  const medications = ((rxRes.data ?? []) as PrescriptionRow[]).map((r) =>
    mapMedication(r, r.provider_id ? (providerName.get(r.provider_id) ?? "—") : "—"),
  );

  const appointments = ((apptsRes.data ?? []) as AppointmentRow[])
    .filter((a) => new Date(a.start_time) > NOW && a.status !== "rescheduled")
    .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
    .map((a) =>
      mapAppointment(a, a.provider_id ? (providerName.get(a.provider_id) ?? "—") : "—"),
    );

  const lastVisitIso = ((apptsRes.data ?? []) as AppointmentRow[])
    .filter((a) => new Date(a.start_time) <= NOW)
    .sort((a, b) => new Date(b.start_time).getTime() - new Date(a.start_time).getTime())[0]
    ?.start_time;

  const patient: Patient = {
    id: p.id,
    mrn: mrnFrom(p.id),
    name: `${p.first_name} ${p.last_name}`,
    firstName: p.first_name,
    lastName: p.last_name,
    dob: fmtDate(p.date_of_birth),
    age: ageFrom(p.date_of_birth),
    phone: p.phone ?? "—",
    pcp: p.preferred_provider_id
      ? (providerName.get(p.preferred_provider_id) ?? "—")
      : "—",
    insurance: p.insurance_plan ?? "—",
    insuranceId: p.insurance_id ?? "—",
    insuranceValid: p.insurance_valid ?? false,
    photoInitials: initials(p.first_name, p.last_name),
    lastVisit: fmtDate(lastVisitIso),
    allergies: [],
    problems: [],
    inrHistory: [],
    medications,
    appointments,
  };

  return { patient, providers };
}
