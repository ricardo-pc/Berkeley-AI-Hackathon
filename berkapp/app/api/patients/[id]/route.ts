import { NextResponse } from "next/server";
import { getPatientBundle } from "../../../_lib/ehr";

// GET /api/patients/[id] — full chart bundle (patient + meds + appts + providers).
export async function GET(
  _req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  try {
    const { id } = await params;
    const bundle = await getPatientBundle(id);
    if (!bundle) {
      return NextResponse.json({ error: "Patient not found" }, { status: 404 });
    }
    return NextResponse.json(bundle);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
