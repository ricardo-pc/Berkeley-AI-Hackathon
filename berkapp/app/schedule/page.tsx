import { ScheduleScreen } from "../_components/schedule/ScheduleScreen";
import { getDaySchedule } from "../_lib/ehr";

// Always read live from Supabase rather than prerendering at build.
export const dynamic = "force-dynamic";

// Demo frame of reference (matches the seeded data / ehr.ts NOW).
const TODAY = "2026-06-20";
// Default to a day that actually has an appointment so the grid isn't empty.
const DEFAULT_DATE = "2026-06-24";

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;

export default async function SchedulePage({
  searchParams,
}: {
  searchParams: Promise<{ date?: string }>;
}) {
  const { date } = await searchParams;
  const selected = date && ISO_DATE.test(date) ? date : DEFAULT_DATE;
  const schedule = await getDaySchedule(selected);

  return <ScheduleScreen date={selected} today={TODAY} schedule={schedule} />;
}
