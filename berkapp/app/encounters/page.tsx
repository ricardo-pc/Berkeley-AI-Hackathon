import { EncountersScreen } from "../_components/encounters/EncountersScreen";
import { getEncounters } from "../_lib/ehr";

// Always read live from Supabase rather than prerendering at build.
export const dynamic = "force-dynamic";

// eClinicalWorks-style Encounters list, backed by the `messages` table.
export default async function EncountersPage() {
  const encounters = await getEncounters();
  return <EncountersScreen encounters={encounters} />;
}
