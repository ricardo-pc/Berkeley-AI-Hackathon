import { NextResponse } from "next/server";
import { fetchTasks } from "@/lib/backend";

// GET /api/tasks — thin proxy to the backend's enriched task list.
export async function GET() {
  try {
    const tasks = await fetchTasks();
    return NextResponse.json(tasks);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
