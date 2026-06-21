"use client";

import { useEffect, useState } from "react";
import type { Task } from "./types";

const REFRESH_INTERVAL_MS = 5_000;

/**
 * Keeps the open dashboard synchronized with Supabase without resetting local
 * UI state such as expanded rows, filters, or scroll position.
 */
export function useLiveTasks(initialTasks: Task[], enabled: boolean) {
  const [tasks, setTasks] = useState<Task[]>(initialTasks);

  useEffect(() => {
    if (!enabled) return;

    let active = true;
    let request: AbortController | null = null;

    async function refresh() {
      if (document.hidden) return;

      request?.abort();
      request = new AbortController();

      try {
        const response = await fetch("/api/tasks", {
          cache: "no-store",
          signal: request.signal,
        });
        if (!response.ok) return;

        const nextTasks: unknown = await response.json();
        if (active && Array.isArray(nextTasks)) {
          setTasks(nextTasks as Task[]);
        }
      } catch (error) {
        if (!(error instanceof DOMException && error.name === "AbortError")) {
          console.error("[dashboard] automatic refresh failed:", error);
        }
      }
    }

    function refreshWhenVisible() {
      if (!document.hidden) void refresh();
    }

    const interval = window.setInterval(() => void refresh(), REFRESH_INTERVAL_MS);
    window.addEventListener("focus", refreshWhenVisible);
    document.addEventListener("visibilitychange", refreshWhenVisible);

    return () => {
      active = false;
      request?.abort();
      window.clearInterval(interval);
      window.removeEventListener("focus", refreshWhenVisible);
      document.removeEventListener("visibilitychange", refreshWhenVisible);
    };
  }, [enabled]);

  return [tasks, setTasks] as const;
}
