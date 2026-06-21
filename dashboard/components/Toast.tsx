"use client";

import { CheckCircle2, Undo2, X } from "lucide-react";

interface ToastProps {
  message: string;
  onUndo?: () => void;
  onDismiss: () => void;
}

export default function Toast({ message, onUndo, onDismiss }: ToastProps) {
  return (
    <div
      role="status"
      aria-live="polite"
      className="fixed inset-x-0 bottom-4 z-50 mx-auto flex w-fit max-w-[calc(100vw-2rem)] items-center gap-3 rounded-[var(--radius)] bg-navy px-4 py-3 text-sm text-white shadow-lg"
    >
      <CheckCircle2 className="size-4 shrink-0 text-success-soft" aria-hidden="true" />
      <span className="font-medium">{message}</span>
      {onUndo && (
        <button
          type="button"
          onClick={onUndo}
          className="inline-flex cursor-pointer items-center gap-1 rounded-[6px] bg-white/15 px-2 py-1 text-xs font-bold hover:bg-white/25"
        >
          <Undo2 className="size-3.5" aria-hidden="true" /> Undo
        </button>
      )}
      <button
        type="button"
        onClick={onDismiss}
        aria-label="Dismiss notification"
        className="cursor-pointer rounded-[6px] p-1 text-white/70 hover:text-white"
      >
        <X className="size-4" aria-hidden="true" />
      </button>
    </div>
  );
}
