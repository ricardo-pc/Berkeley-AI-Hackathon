"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import type { PatientSummary } from "../_lib/types";
import { Panel } from "./ui";

export function PatientListTable({ patients }: { patients: PatientSummary[] }) {
  const router = useRouter();
  const [q, setQ] = useState("");

  const filtered = patients.filter((p) => {
    const t = q.toLowerCase();
    return (
      p.name.toLowerCase().includes(t) ||
      p.mrn.toLowerCase().includes(t) ||
      p.dob.includes(t)
    );
  });

  return (
    <div className="overflow-y-auto p-4">
      <div className="mb-3 flex items-center justify-between">
        <h1 className="text-lg font-semibold text-slate-700">Patient Lookup</h1>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Filter by name / DOB / MRN…"
          className="w-72 rounded border border-slate-300 px-2 py-1.5 text-xs focus:border-sky-500 focus:outline-none"
        />
      </div>

      <Panel title={`Patients (${filtered.length})`}>
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-slate-300 text-left text-slate-500">
              <th className="py-1.5 font-medium">Name</th>
              <th className="py-1.5 font-medium">DOB</th>
              <th className="py-1.5 font-medium">Age</th>
              <th className="py-1.5 font-medium">MRN</th>
              <th className="py-1.5 font-medium">PCP</th>
              <th className="py-1.5 font-medium">Last visit</th>
              <th className="py-1.5 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((p) => (
              <tr
                key={p.id}
                onClick={() => router.push(`/ehr/${p.id}`)}
                className="cursor-pointer border-b border-slate-100 hover:bg-sky-50"
              >
                <td className="py-2">
                  <div className="flex items-center gap-2">
                    <span className="flex h-7 w-7 items-center justify-center rounded bg-gradient-to-br from-slate-500 to-slate-700 text-[10px] font-bold text-white">
                      {p.photoInitials}
                    </span>
                    <span className="font-semibold text-sky-800">{p.name}</span>
                  </div>
                </td>
                <td className="py-2 text-slate-600">{p.dob}</td>
                <td className="py-2 text-slate-600">{p.age}</td>
                <td className="py-2 text-slate-500">{p.mrn}</td>
                <td className="py-2 text-slate-600">{p.pcp}</td>
                <td className="py-2 text-slate-500">{p.lastVisit}</td>
                <td className="py-2">
                  {p.flag && (
                    <span className="rounded bg-amber-100 px-1.5 py-0.5 text-[10px] font-semibold text-amber-700">
                      {p.flag}
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <p className="py-6 text-center text-xs text-slate-400">No patients match.</p>
        )}
      </Panel>

      <p className="mt-3 text-[11px] text-slate-400">
        Each row is a chart a front-desk worker has to open and work through by hand
        for every voicemail. Click a patient to enter their chart.
      </p>
    </div>
  );
}
