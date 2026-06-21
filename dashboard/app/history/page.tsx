import AppShell from "@/components/AppShell";
import HistoryTable from "@/components/HistoryTable";
import { fetchTasks } from "@/lib/backend";

export const dynamic = "force-dynamic";

export default async function HistoryPage() {
  const tasks = await fetchTasks();

  return (
    <AppShell
      chwName="Chris Kim"
      active="history"
      usingFixtures={false}
      title="Decision history"
      subtitle="Every request you've approved, rejected, or handled — filter and review past decisions."
    >
      <HistoryTable tasks={tasks} usingFixtures={false} />
    </AppShell>
  );
}
