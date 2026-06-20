"use client";

// Resolves the "active patient" for the chart from the URL (/ehr/[id]/...).
// Today it reads from the hardcoded patients array; when Supabase lands, only
// this lookup changes — every screen keeps calling useActivePatient().

import { createContext, useContext } from "react";
import { useParams } from "next/navigation";
import { getPatient, type Patient } from "../_lib/data";

const PatientContext = createContext<Patient | null>(null);

export function PatientProvider({ children }: { children: React.ReactNode }) {
  const params = useParams<{ id: string }>();
  const patient = params?.id ? getPatient(params.id) ?? null : null;
  return (
    <PatientContext.Provider value={patient}>{children}</PatientContext.Provider>
  );
}

export function useActivePatient(): Patient {
  const p = useContext(PatientContext);
  if (!p) {
    throw new Error(
      "No active patient in context (used outside /ehr/[id] or unknown id)",
    );
  }
  return p;
}

// Nullable variant for the chart shell, which must render a "not found" state
// rather than throwing when the URL id doesn't match a patient.
export function usePatientOrNull(): Patient | null {
  return useContext(PatientContext);
}
