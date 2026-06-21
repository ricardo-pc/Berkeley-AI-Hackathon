"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

const REFRESH_INTERVAL_MS = 5_000;

/**
 * Re-runs the active Server Component route so its Supabase queries stay
 * current. Next.js merges the result without discarding client or scroll state.
 */
export function AutoRefresh() {
  const router = useRouter();

  useEffect(() => {
    function refreshWhenVisible() {
      if (!document.hidden) router.refresh();
    }

    const interval = window.setInterval(refreshWhenVisible, REFRESH_INTERVAL_MS);
    window.addEventListener("focus", refreshWhenVisible);
    document.addEventListener("visibilitychange", refreshWhenVisible);

    return () => {
      window.clearInterval(interval);
      window.removeEventListener("focus", refreshWhenVisible);
      document.removeEventListener("visibilitychange", refreshWhenVisible);
    };
  }, [router]);

  return null;
}
