import { NextResponse } from "next/server";
import { getTasks } from "@/lib/tasks-repo";

// GET /api/tasks — all tasks, enriched + mapped. Used for client-side refetch.
export async function GET() {
  try {
    const tasks = await getTasks();
    return NextResponse.json(tasks);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
