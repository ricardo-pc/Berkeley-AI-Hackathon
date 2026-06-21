"use client";

// Holds the active patient + practice providers for the chart, fetched on the
// server (from Supabase) and handed down to the client components that render
// the chart. When the data source changes, only ehr.ts / the layout change —
// every screen keeps calling useActivePatient() / useProviders().

import { createContext, useContext } from "react";
import type { Patient, Provider } from "../_lib/types";

type ChartData = { patient: Patient | null; providers: Provider[] };

const ChartContext = createContext<ChartData | null>(null);

export function PatientProvider({
  patient,
  providers,
  children,
}: {
  patient: Patient | null;
  providers: Provider[];
  children: React.ReactNode;
}) {
  return (
    <ChartContext.Provider value={{ patient, providers }}>
      {children}
    </ChartContext.Provider>
  );
}

export function useActivePatient(): Patient {
  const ctx = useContext(ChartContext);
  if (!ctx?.patient) {
    throw new Error(
      "No active patient in context (used outside /ehr/[id] or unknown id)",
    );
  }
  return ctx.patient;
}

export function usePatientOrNull(): Patient | null {
  return useContext(ChartContext)?.patient ?? null;
}

export function useProviders(): Provider[] {
  return useContext(ChartContext)?.providers ?? [];
}
