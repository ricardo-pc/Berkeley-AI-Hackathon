import { NextResponse } from "next/server";
import { getPatients } from "../../_lib/ehr";

// GET /api/patients — patient list for the EHR lookup screen.
export async function GET() {
  try {
    const patients = await getPatients();
    return NextResponse.json({ patients });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
