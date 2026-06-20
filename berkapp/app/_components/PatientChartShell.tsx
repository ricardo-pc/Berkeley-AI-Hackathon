"use client";

import Link from "next/link";
import { usePatientOrNull } from "./PatientContext";
import { LeftNav, PatientBanner } from "./Shell";

// Renders the patient-scoped chrome (banner + left nav) around a chart page,
// or a graceful "not found" state for an unknown patient id.
export function PatientChartShell({ children }: { children: React.ReactNode }) {
  const patient = usePatientOrNull();

  if (!patient) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-3 p-10 text-center">
        <div className="text-3xl">🔍</div>
        <p className="text-sm text-slate-600">
          No patient found for this chart.
        </p>
        <Link href="/ehr" className="text-xs text-sky-700 underline">
          ← Back to patient list
        </Link>
      </div>
    );
  }

  return (
    <>
      <PatientBanner />
      <div className="flex min-h-0 flex-1">
        <LeftNav />
        <main className="min-w-0 flex-1 overflow-y-auto bg-slate-100 p-4">
          {children}
        </main>
      </div>
    </>
  );
}
