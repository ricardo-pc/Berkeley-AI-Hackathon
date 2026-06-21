import DashboardClient from "@/components/DashboardClient";
import { getTasks } from "@/lib/tasks-repo";
import { SEED_TASKS } from "@/lib/mockData";

// Always read live task state (no static caching of the queue).
export const dynamic = "force-dynamic";

export default async function Home() {
  let initialTasks = SEED_TASKS;
  let usingFixtures = true;
  try {
    const tasks = await getTasks();
    // If the table is empty, keep the fixtures so the demo isn't blank.
    if (tasks.length > 0) {
      initialTasks = tasks;
      usingFixtures = false;
    }
  } catch (err) {
    // No env / unreachable DB → fall back to fixtures rather than crashing.
    console.error("[dashboard] falling back to fixtures:", err);
  }

  return <DashboardClient initialTasks={initialTasks} usingFixtures={usingFixtures} />;
}
