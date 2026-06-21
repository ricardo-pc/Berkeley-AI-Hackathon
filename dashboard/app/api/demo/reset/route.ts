import { NextResponse } from "next/server";
import { resetDemo } from "@/lib/backend";

// POST /api/demo/reset — restore the demo to its saved baseline (Reset button).
export async function POST() {
  try {
    return NextResponse.json(await resetDemo());
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
