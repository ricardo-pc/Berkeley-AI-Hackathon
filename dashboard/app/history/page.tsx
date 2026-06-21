import AppHeader from "@/components/AppHeader";
import HistoryTable from "@/components/HistoryTable";
import { getTasks } from "@/lib/tasks-repo";
import { SEED_TASKS } from "@/lib/mockData";
import { isDecided } from "@/lib/task";

export const dynamic = "force-dynamic";

export default async function HistoryPage() {
  let tasks = SEED_TASKS;
  let usingFixtures = true;
  try {
    const live = await getTasks();
    if (live.length > 0) {
      tasks = live;
      usingFixtures = false;
    }
  } catch (err) {
    console.error("[history] falling back to fixtures:", err);
  }

  const decided = tasks.filter(isDecided);

  return (
    <div className="flex min-h-full flex-col">
      <AppHeader chwName="Riya Shah" active="history" />
      {usingFixtures && (
        <div className="bg-warning-soft px-4 py-1.5 text-center text-xs font-semibold text-accent">
          Demo data — not connected to the live database
        </div>
      )}
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 sm:px-6">
        <div className="mb-4">
          <h2 className="text-base font-bold text-navy">Decision history</h2>
          <p className="text-sm text-muted-foreground">
            Every request you&rsquo;ve approved, rejected, or handled — filter and review past decisions.
          </p>
        </div>
        <HistoryTable tasks={decided} />
      </main>
    </div>
  );
}
