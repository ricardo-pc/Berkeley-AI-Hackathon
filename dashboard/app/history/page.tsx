import AppShell from "@/components/AppShell";
import HistoryTable from "@/components/HistoryTable";
import { fetchTasks } from "@/lib/backend";
import { SEED_TASKS } from "@/lib/mockData";

export const dynamic = "force-dynamic";

export default async function HistoryPage() {
  let tasks = SEED_TASKS;
  let usingFixtures = true;
  try {
    const live = await fetchTasks();
    if (live.length > 0) {
      tasks = live;
      usingFixtures = false;
    }
  } catch (err) {
    console.error("[history] falling back to fixtures:", err);
  }

  return (
    <AppShell
      chwName="Riya Shah"
      active="history"
      usingFixtures={usingFixtures}
      title="Decision history"
      subtitle="Every request you've approved, rejected, or handled — filter and review past decisions."
    >
      <HistoryTable tasks={tasks} usingFixtures={usingFixtures} />
    </AppShell>
  );
}
