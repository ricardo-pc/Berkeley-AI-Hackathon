import { ManageOrders } from "../_components/rx/ManageOrders";
import { getPatientBundle } from "../_lib/ehr";

// Always read live from Supabase rather than prerendering at build.
export const dynamic = "force-dynamic";

// "Manage Orders → Add New Rx" screen for a specific patient. The nav only
// links here with a patientId once a chart is open; a direct hit without one
// renders an empty-state prompt.
export default async function RxPage({
  searchParams,
}: {
  searchParams: Promise<{ patientId?: string }>;
}) {
  const { patientId } = await searchParams;
  const bundle = patientId ? await getPatientBundle(patientId) : null;
  return <ManageOrders patient={bundle?.patient ?? null} />;
}
