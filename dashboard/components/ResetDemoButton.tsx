"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { RotateCcw, Loader2 } from "lucide-react";

// Restores the demo to its saved baseline via the backend, then refreshes the
// server-rendered queue. Lets a CHW re-run the same demo scenario cleanly.
export default function ResetDemoButton() {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [busy, setBusy] = useState(false);

  async function reset() {
    if (busy || pending) return;
    if (!window.confirm("Reset the demo to its baseline? This undoes test approvals/rejections.")) return;
    setBusy(true);
    try {
      const res = await fetch("/api/demo/reset", { method: "POST" });
      if (!res.ok) throw new Error(`Reset failed (${res.status})`);
      startTransition(() => router.refresh());
    } catch (err) {
      window.alert(err instanceof Error ? err.message : "Reset failed");
    } finally {
      setBusy(false);
    }
  }

  const working = busy || pending;
  return (
    <button
      type="button"
      onClick={reset}
      disabled={working}
      className="inline-flex items-center gap-1.5 self-start rounded-full border border-border bg-surface px-3 py-1 text-xs font-semibold text-muted-foreground transition-colors hover:border-primary hover:text-primary disabled:cursor-wait disabled:opacity-70 sm:self-auto"
    >
      {working ? <Loader2 className="size-3.5 animate-spin" aria-hidden="true" /> : <RotateCcw className="size-3.5" aria-hidden="true" />}
      {working ? "Resetting…" : "Reset demo"}
    </button>
  );
}
