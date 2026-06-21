import "server-only";

import { supabaseAdmin } from "./supabase";
import type { ProposedAction, Task, TaskStatus, TaskType } from "./types";

// ---- DB row shapes (what Supabase returns) ----
// The `tasks` table has NO patient_name column — name/dob/phone come from a
// `patients` join (via patient_id), and the transcript from a `voicemails` join
// (via voicemail_id). Audit columns approved_at/approved_by exist; chw_note /
// reviewed_at / rejected_at are added by db/migrations/0001_chw_decision_columns.sql.

type TaskRow = {
  id: string;
  patient_id: string | null;
  voicemail_id: string | null;
  task_type: string | null;
  status: string | null;
  agent_summary: string | null;
  agent_checks: Record<string, unknown> | null;
  proposed_action: ProposedAction | null;
  flagged_reason: string | null;
  created_at: string;
  chw_note?: string | null;
  reviewed_at?: string | null;
  approved_at?: string | null;
  approved_by?: string | null;
  rejected_at?: string | null;
};

type PatientRow = {
  id: string;
  first_name: string | null;
  last_name: string | null;
  date_of_birth: string | null;
  phone: string | null;
};

type VoicemailRow = { id: string; transcript: string | null; audio_url: string | null };

const ACTIONABLE = new Set(["prescription_refill", "reschedule", "message_relay", "escalate"]);
const KNOWN_STATUS = new Set(["pending_approval", "escalated", "rejected", "complete"]);

function mapRow(
  row: TaskRow,
  patients: Map<string, PatientRow>,
  voicemails: Map<string, VoicemailRow>,
): Task {
  const patient = row.patient_id ? patients.get(row.patient_id) : undefined;
  const vm = row.voicemail_id ? voicemails.get(row.voicemail_id) : undefined;
  const name = patient
    ? [patient.first_name, patient.last_name].filter(Boolean).join(" ").trim()
    : "Unknown patient";

  return {
    id: row.id,
    patient_id: row.patient_id,
    patient_name: name || "Unknown patient",
    task_type: (ACTIONABLE.has(row.task_type ?? "") ? row.task_type : "escalate") as TaskType,
    status: (KNOWN_STATUS.has(row.status ?? "") ? row.status : "escalated") as TaskStatus,
    agent_summary: row.agent_summary ?? "",
    agent_checks: row.agent_checks ?? {},
    proposed_action: row.proposed_action ?? null,
    flagged_reason: row.flagged_reason,
    created_at: row.created_at,
    chw_note: row.chw_note ?? null,
    reviewed_at: row.reviewed_at ?? null,
    approved_at: row.approved_at ?? null,
    rejected_at: row.rejected_at ?? null,
    transcript: vm?.transcript ?? undefined,
    patient_dob: patient?.date_of_birth ?? undefined,
    patient_phone: patient?.phone ?? undefined,
  };
}

/** All tasks, enriched with patient + voicemail data, newest first. */
export async function getTasks(): Promise<Task[]> {
  const sb = supabaseAdmin();
  const { data: rows, error } = await sb
    .from("tasks")
    .select("*")
    .order("created_at", { ascending: false });
  if (error) throw new Error(`Failed to load tasks: ${error.message}`);

  const taskRows = (rows ?? []) as TaskRow[];
  const patientIds = [...new Set(taskRows.map((r) => r.patient_id).filter(Boolean))] as string[];
  const voicemailIds = [...new Set(taskRows.map((r) => r.voicemail_id).filter(Boolean))] as string[];

  const [patientsRes, voicemailsRes] = await Promise.all([
    patientIds.length
      ? sb.from("patients").select("id, first_name, last_name, date_of_birth, phone").in("id", patientIds)
      : Promise.resolve({ data: [] as PatientRow[] }),
    voicemailIds.length
      ? sb.from("voicemails").select("id, transcript, audio_url").in("id", voicemailIds)
      : Promise.resolve({ data: [] as VoicemailRow[] }),
  ]);

  const patients = new Map((patientsRes.data ?? []).map((p) => [p.id as string, p as PatientRow]));
  const voicemails = new Map((voicemailsRes.data ?? []).map((v) => [v.id as string, v as VoicemailRow]));

  return taskRows.map((r) => mapRow(r, patients, voicemails));
}

/** Read one task (with joins) → mapped Task, or null. */
export async function getTask(id: string): Promise<Task | null> {
  const sb = supabaseAdmin();
  const { data: rows, error } = await sb.from("tasks").select("*").eq("id", id).limit(1);
  if (error) throw new Error(`Failed to read task: ${error.message}`);
  if (!rows?.length) return null;
  const row = rows[0] as TaskRow;

  const patients = new Map<string, PatientRow>();
  if (row.patient_id) {
    const { data } = await sb
      .from("patients")
      .select("id, first_name, last_name, date_of_birth, phone")
      .eq("id", row.patient_id)
      .limit(1);
    if (data?.[0]) patients.set(row.patient_id, data[0] as PatientRow);
  }
  const voicemails = new Map<string, VoicemailRow>();
  if (row.voicemail_id) {
    const { data } = await sb
      .from("voicemails")
      .select("id, transcript, audio_url")
      .eq("id", row.voicemail_id)
      .limit(1);
    if (data?.[0]) voicemails.set(row.voicemail_id, data[0] as VoicemailRow);
  }
  return mapRow(row, patients, voicemails);
}

/** First/last/dob for an executor request (patient_id is the canonical key). */
export async function getPatientIdentity(
  patientId: string,
): Promise<{ first_name: string; last_name: string; dob: string }> {
  const sb = supabaseAdmin();
  const { data } = await sb
    .from("patients")
    .select("first_name, last_name, date_of_birth")
    .eq("id", patientId)
    .limit(1);
  const p = data?.[0] as PatientRow | undefined;
  return {
    first_name: p?.first_name ?? "",
    last_name: p?.last_name ?? "",
    dob: p?.date_of_birth ?? "",
  };
}

/** Columns the dashboard is allowed to write on a CHW decision. */
export type TaskDecisionPatch = Partial<
  Pick<TaskRow, "status" | "chw_note" | "reviewed_at" | "approved_at" | "approved_by" | "rejected_at">
>;

export async function patchTask(id: string, patch: TaskDecisionPatch): Promise<Task> {
  const sb = supabaseAdmin();
  const { error } = await sb.from("tasks").update(patch).eq("id", id);
  if (error) throw new Error(`Failed to update task: ${error.message}`);
  const task = await getTask(id);
  if (!task) throw new Error("Task not found after update");
  return task;
}
