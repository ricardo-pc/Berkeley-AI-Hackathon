import DashboardClient from "@/components/DashboardClient";
import { fetchTasks } from "@/lib/backend";

// Always read live task state (no static caching of the queue).
export const dynamic = "force-dynamic";

export default async function Home() {
  const initialTasks = await fetchTasks();

  return <DashboardClient initialTasks={initialTasks} usingFixtures={false} />;
}
