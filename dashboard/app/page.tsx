import DashboardClient from "@/components/DashboardClient";
import { fetchTasks } from "@/lib/backend";
import { SEED_TASKS } from "@/lib/mockData";

// Always read live task state (no static caching of the queue).
export const dynamic = "force-dynamic";

export default async function Home() {
  let initialTasks = SEED_TASKS;
  let usingFixtures = true;
  try {
    const tasks = await fetchTasks();
    // If the backend returns nothing, keep the fixtures so the demo isn't blank.
    if (tasks.length > 0) {
      initialTasks = tasks;
      usingFixtures = false;
    }
  } catch (err) {
    // Backend unreachable → fall back to fixtures rather than crashing.
    console.error("[dashboard] falling back to fixtures:", err);
  }

  return <DashboardClient initialTasks={initialTasks} usingFixtures={usingFixtures} />;
}
