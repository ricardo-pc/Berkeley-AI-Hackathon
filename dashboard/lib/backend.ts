import "server-only";

import type { Task } from "./types";

const BASE = process.env.BACKEND_API_URL?.replace(/\/$/, "");

export type Decision = "approve" | "reject" | "action_taken" | "mark_done" | "reopen";

export class BackendUnavailableError extends Error {}

function base(): string {
  if (!BASE) throw new BackendUnavailableError("BACKEND_API_URL is not set");
  return BASE;
}

/** Enriched task list from the backend (already in the UI `Task` shape). */
export async function fetchTasks(): Promise<Task[]> {
  const res = await fetch(`${base()}/api/tasks`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Backend GET /api/tasks failed (${res.status})`);
  return (await res.json()) as Task[];
}

/** Apply a CHW decision. Returns the updated task + a human-facing notice. */
export async function postDecision(
  id: string,
  body: { decision: Decision; note?: string; status?: string; chw?: string },
): Promise<{ task: Task; notice?: string }> {
  const res = await fetch(`${base()}/api/tasks/${id}/decision`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    cache: "no-store",
  });
  if (!res.ok) {
    const detail = (await res.json().catch(() => ({}))) as { detail?: string; error?: string };
    throw new Error(detail.detail ?? detail.error ?? `Decision failed (${res.status})`);
  }
  return (await res.json()) as { task: Task; notice?: string };
}

/** Restore the demo to its saved baseline (Reset button). */
export async function resetDemo(): Promise<{ reset: boolean; [k: string]: unknown }> {
  const res = await fetch(`${base()}/api/demo/reset`, { method: "POST", cache: "no-store" });
  if (!res.ok) throw new Error(`Backend reset failed (${res.status})`);
  return (await res.json()) as { reset: boolean };
}
