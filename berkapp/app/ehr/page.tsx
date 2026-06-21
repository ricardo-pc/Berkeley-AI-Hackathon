import { PatientListTable } from "../_components/PatientListTable";
import { getPatients } from "../_lib/ehr";

// Always read live from Supabase rather than prerendering at build.
export const dynamic = "force-dynamic";

// Server component: pulls the patient list from Supabase, hands it to the
// client table for search/navigation.
export default async function PatientListPage() {
  const patients = await getPatients();
  return <PatientListTable patients={patients} />;
}
