"use client";

// Small shared UI primitives styled to feel like a dense, slightly dated
// clinical app (eClinicalWorks vibe): small fonts, hard borders, gray chrome,
// blue section headers, chunky little buttons.

import { useEffect } from "react";

export function Panel({
  title,
  children,
  className = "",
  right,
}: {
  title?: string;
  children: React.ReactNode;
  className?: string;
  right?: React.ReactNode;
}) {
  return (
    <div className={`border border-slate-300 bg-white shadow-sm ${className}`}>
      {title && (
        <div className="flex items-center justify-between bg-gradient-to-b from-slate-100 to-slate-200 px-3 py-1.5">
          <h2 className="text-[13px] font-semibold uppercase tracking-wide text-slate-700">
            {title}
          </h2>
          {right}
        </div>
      )}
      <div className="p-3">{children}</div>
    </div>
  );
}

type BtnVariant = "primary" | "default" | "danger" | "ghost";

export function Button({
  children,
  onClick,
  variant = "default",
  type = "button",
  disabled,
  className = "",
}: {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: BtnVariant;
  type?: "button" | "submit";
  disabled?: boolean;
  className?: string;
}) {
  const base =
    "inline-flex items-center justify-center gap-1.5 rounded border px-3 py-1.5 text-xs font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-50";
  const styles: Record<BtnVariant, string> = {
    primary:
      "border-sky-700 bg-gradient-to-b from-sky-600 to-sky-700 text-white hover:from-sky-700 hover:to-sky-800",
    default:
      "border-slate-400 bg-gradient-to-b from-white to-slate-100 text-slate-700 hover:from-slate-50 hover:to-slate-200",
    danger:
      "border-rose-700 bg-gradient-to-b from-rose-600 to-rose-700 text-white hover:from-rose-700 hover:to-rose-800",
    ghost: "border-transparent bg-transparent text-sky-700 hover:underline",
  };
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`${base} ${styles[variant]} ${className}`}
    >
      {children}
    </button>
  );
}

export function Field({
  label,
  children,
  required,
}: {
  label: string;
  children: React.ReactNode;
  required?: boolean;
}) {
  return (
    <label className="block">
      <span className="mb-0.5 block text-[11px] font-semibold uppercase tracking-wide text-slate-500">
        {label} {required && <span className="text-rose-600">*</span>}
      </span>
      {children}
    </label>
  );
}

const inputCls =
  "w-full rounded border border-slate-300 bg-white px-2 py-1.5 text-xs text-slate-800 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-300";

export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} className={`${inputCls} ${props.className ?? ""}`} />;
}

export function Select(props: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return <select {...props} className={`${inputCls} ${props.className ?? ""}`} />;
}

export function Textarea(props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea {...props} className={`${inputCls} min-h-[80px] ${props.className ?? ""}`} />
  );
}

export function Modal({
  title,
  children,
  onClose,
  width = "max-w-lg",
}: {
  title: string;
  children: React.ReactNode;
  onClose: () => void;
  width?: string;
}) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-40 flex items-start justify-center bg-black/40 p-6 pt-20">
      <div className={`w-full ${width} border border-slate-400 bg-white shadow-2xl`}>
        <div className="flex items-center justify-between bg-gradient-to-b from-sky-700 to-sky-800 px-4 py-2 text-white">
          <h3 className="text-sm font-semibold">{title}</h3>
          <button onClick={onClose} aria-label="Close" className="hover:text-sky-200">
            ✕
          </button>
        </div>
        <div className="max-h-[70vh] overflow-y-auto p-4">{children}</div>
      </div>
    </div>
  );
}

export function Stepper({ steps, current }: { steps: string[]; current: number }) {
  return (
    <ol className="mb-4 flex items-center gap-1 text-[11px]">
      {steps.map((s, i) => (
        <li key={s} className="flex items-center gap-1">
          <span
            className={`flex h-5 w-5 items-center justify-center rounded-full font-bold ${
              i < current
                ? "bg-emerald-600 text-white"
                : i === current
                  ? "bg-sky-700 text-white"
                  : "bg-slate-200 text-slate-500"
            }`}
          >
            {i < current ? "✓" : i + 1}
          </span>
          <span
            className={i === current ? "font-semibold text-slate-800" : "text-slate-500"}
          >
            {s}
          </span>
          {i < steps.length - 1 && <span className="px-1 text-slate-300">›</span>}
        </li>
      ))}
    </ol>
  );
}
