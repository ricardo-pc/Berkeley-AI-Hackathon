import { NextResponse } from "next/server";
import { postDecision, type Decision } from "@/lib/backend";

const DECISIONS = new Set<Decision>(["approve", "reject", "action_taken", "mark_done", "reopen"]);

// PATCH /api/tasks/[id] — thin proxy to the backend decision executor.
// The backend is authoritative for the status lifecycle + all DB writes.
export async function PATCH(req: Request, { params }: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await params;
    const body = (await req.json()) as { decision?: Decision; note?: string; status?: string };
    if (!body.decision || !DECISIONS.has(body.decision)) {
      return NextResponse.json({ error: "Invalid or missing `decision`." }, { status: 400 });
    }
    const result = await postDecision(id, {
      decision: body.decision,
      note: body.note,
      status: body.status,
    });
    return NextResponse.json(result);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
