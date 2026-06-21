"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import type { Medication, Patient, Problem } from "../../_lib/types";

// eClinicalWorks "Manage Orders → Add New Rx" screen, populated with the active
// patient's real data (identity, coded problems, and current medications) from
// Supabase. The surrounding chrome (tabs, toolbar, footer) is illustrative.

const TABS = ["Medication Summary", "Add New Rx", "Add New Order"];

export function ManageOrders({ patient }: { patient: Patient | null }) {
  const router = useRouter();
  const close = () => router.back();

  const [tab, setTab] = useState("Add New Rx");
  const [checked, setChecked] = useState<Set<string>>(() => new Set());
  const toggle = (code: string) =>
    setChecked((prev) => {
      const next = new Set(prev);
      next.has(code) ? next.delete(code) : next.add(code);
      return next;
    });

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-slate-900/40 p-3">
      <div className="flex h-[95vh] w-full max-w-[1480px] flex-col overflow-hidden rounded-md border border-slate-400 bg-white shadow-2xl">
        {/* ---- title bar ---- */}
        <div className="flex flex-shrink-0 items-center gap-2 bg-gradient-to-b from-sky-500 to-sky-600 px-4 py-2 text-white">
          <span className="text-sm font-semibold">Manage Orders</span>
          {patient ? (
            <>
              <span className="text-sm font-semibold">
                {patient.lastName}, {patient.firstName}
              </span>
              <span aria-hidden>👤</span>
              <span className="text-xs">
                DOB {patient.dob} ({patient.age} yo
                {patient.sex ? ` ${patient.sex.charAt(0).toUpperCase()}` : ""})
              </span>
              <span aria-hidden>🚩</span>
              <span className="text-xs">Acc No. {patient.mrn}</span>
            </>
          ) : (
            <span className="text-xs text-white/80">No patient selected</span>
          )}
          <button
            onClick={close}
            aria-label="Close"
            className="ml-auto flex h-6 w-6 items-center justify-center rounded-full bg-sky-700/60 text-sm hover:bg-sky-800"
          >
            ✕
          </button>
        </div>

        {/* ---- tab strip ---- */}
        <div className="flex flex-shrink-0 justify-end gap-px border-b border-slate-300 bg-sky-600 px-3 pt-1.5">
          {TABS.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`rounded-t px-4 py-1.5 text-xs font-semibold ${
                tab === t ? "bg-white text-sky-700" : "text-white/90 hover:bg-white/15"
              }`}
            >
              {t}
            </button>
          ))}
        </div>

        {/* ---- body ---- */}
        {!patient ? (
          <div className="flex flex-1 flex-col items-center justify-center gap-2 text-sm text-slate-400">
            <span className="text-3xl" aria-hidden>📋</span>
            Open a patient chart, then choose Rx to manage their orders.
          </div>
        ) : tab === "Add New Rx" ? (
          <div className="flex min-h-0 flex-1">
            <AssessmentsSidebar problems={patient.problems} checked={checked} onToggle={toggle} />
            <RxMain patient={patient} />
          </div>
        ) : (
          <div className="flex flex-1 items-center justify-center text-sm text-slate-400">
            {tab} — not part of this demo screen.
          </div>
        )}

        {/* ---- footer ---- */}
        <div className="flex flex-shrink-0 items-center justify-between border-t border-slate-300 bg-slate-100 px-4 py-2">
          <div className="flex">
            <button className="rounded-l border border-slate-400 bg-gradient-to-b from-white to-slate-100 px-4 py-1.5 text-xs font-semibold text-slate-700 hover:from-slate-50 hover:to-slate-200">
              Send
            </button>
            <button className="rounded-r border border-l-0 border-slate-400 bg-gradient-to-b from-white to-slate-100 px-1.5 py-1.5 text-[10px] text-slate-600 hover:from-slate-50 hover:to-slate-200">
              ▲
            </button>
          </div>
          <div className="flex gap-2">
            <button className="rounded border border-rose-700 bg-gradient-to-b from-rose-500 to-rose-600 px-4 py-1.5 text-xs font-semibold text-white hover:from-rose-600 hover:to-rose-700">
              Allergies{patient && patient.allergies.length ? ` (${patient.allergies.length})` : ""}
            </button>
            <button
              onClick={close}
              className="rounded border border-sky-700 bg-gradient-to-b from-sky-500 to-sky-600 px-6 py-1.5 text-xs font-semibold text-white hover:from-sky-600 hover:to-sky-700"
            >
              OK
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ------------------------------------------------------------- assessments
function AssessmentsSidebar({
  problems,
  checked,
  onToggle,
}: {
  problems: Problem[];
  checked: Set<string>;
  onToggle: (code: string) => void;
}) {
  const items = [
    ...problems.map((p) => ({ code: p.code, text: p.description })),
    { code: "N/A", text: "Other" },
  ];
  return (
    <aside className="w-64 flex-shrink-0 overflow-y-auto border-r border-slate-300 bg-sky-50 p-3">
      <div className="mb-3 flex items-center gap-2">
        <span className="text-xs font-bold uppercase tracking-wide text-sky-700">Assessments</span>
        <button className="flex h-5 w-5 items-center justify-center rounded border border-slate-400 bg-white text-xs text-slate-600 hover:bg-slate-50">
          ＋
        </button>
      </div>
      {problems.length === 0 && (
        <p className="mb-2 text-[11px] italic text-slate-400">No coded problems on file.</p>
      )}
      <ul className="space-y-3">
        {items.map((a) => (
          <li key={a.code}>
            <label className="flex gap-2 text-xs text-slate-700">
              <input
                type="checkbox"
                checked={checked.has(a.code)}
                onChange={() => onToggle(a.code)}
                className="mt-0.5"
              />
              <span>
                <b className="text-slate-800">{a.code}</b>{"  "}
                {a.text}
              </span>
            </label>
          </li>
        ))}
      </ul>
    </aside>
  );
}

// ------------------------------------------------------------- Rx main panel
function RedD() {
  return (
    <span className="flex h-5 w-5 items-center justify-center rounded-full bg-rose-600 text-[10px] font-bold text-white">
      D
    </span>
  );
}

const MED_COLS = ["Medication", "Strength", "SIG", "Refills", "Last Filled", "Prescriber", "Status"];

function RxMain({ patient }: { patient: Patient }) {
  const toolBtn =
    "flex h-7 w-7 items-center justify-center rounded border border-slate-300 bg-white text-xs text-slate-600 hover:bg-slate-50";
  const meds = patient.medications;
  const activeCount = meds.filter((m) => m.status === "Active").length;

  return (
    <div className="flex min-w-0 flex-1 flex-col overflow-auto bg-white">
      {/* toolbar */}
      <div className="flex flex-shrink-0 items-center gap-2 border-b border-slate-200 px-3 py-2">
        <div className="flex items-center rounded border border-slate-300 bg-white px-2">
          <input
            placeholder="Quick Search"
            className="w-44 py-1 text-xs text-slate-700 focus:outline-none"
          />
          <button className="text-slate-400 hover:text-slate-600" aria-label="Clear">✕</button>
        </div>
        <button className={toolBtn} aria-label="Previous">‹</button>
        <button className={toolBtn} aria-label="Next">›</button>
        <button className={toolBtn} aria-label="Favorite">★</button>
        <button className={toolBtn} aria-label="Filter">▽</button>
        <button
          className="flex h-7 w-7 items-center justify-center rounded border border-sky-400 bg-sky-100 text-xs text-sky-700"
          aria-label="Chart"
        >
          📈
        </button>
        <button className={toolBtn} aria-label="Help">?</button>

        <div className="ml-1 text-sm font-bold text-slate-800">
          Current Medications{" "}
          <span className="text-xs font-normal text-slate-500">
            ({activeCount} active / {meds.length} total)
          </span>
        </div>

        <div className="ml-auto flex items-center gap-2">
          <button className="rounded border border-slate-300 bg-white px-2.5 py-1 text-xs font-semibold text-emerald-700 hover:bg-slate-50">
            ✓ Rx Eligibility
          </button>
          <button className="rounded border border-slate-300 bg-white px-2.5 py-1 text-xs font-semibold text-slate-700 hover:bg-slate-50">
            PDMP
          </button>
          <button className="rounded border border-slate-300 bg-white px-2.5 py-1 text-xs font-semibold text-slate-700 hover:bg-slate-50">
            New ▾
          </button>
        </div>
      </div>

      {/* medications table */}
      <div className="px-3 pt-2">
        <table className="w-full border-collapse text-xs">
          <thead>
            <tr className="border-b border-slate-300 bg-slate-50 text-left text-slate-600">
              <th className="w-7 px-1 py-1.5 text-center"><RedD /></th>
              <th className="w-6 px-1 py-1.5 text-center text-sky-600">✎</th>
              <th className="w-6 px-1 py-1.5 text-center text-amber-400">★</th>
              {MED_COLS.map((c) => (
                <th key={c} className="px-2 py-1.5 font-medium">{c}</th>
              ))}
              <th className="w-8 px-2 py-1.5" />
            </tr>
          </thead>
          <tbody>
            {meds.length === 0 ? (
              <tr>
                <td colSpan={3 + MED_COLS.length + 1} className="px-2 py-6 text-center text-slate-400">
                  No medications on file for this patient.
                </td>
              </tr>
            ) : (
              meds.map((m) => <MedRow key={m.id} m={m} />)
            )}
          </tbody>
        </table>
        <p className="mt-3 text-[11px] text-slate-400">
          Every refill voicemail means opening this list, finding the exact drug,
          checking the date and remaining refills, and re-keying the order by hand.
        </p>
      </div>
    </div>
  );
}

function MedRow({ m }: { m: Medication }) {
  return (
    <tr className="border-b border-slate-200 text-slate-700">
      <td className="px-1 py-2 text-center">
        <div className="flex justify-center"><RedD /></div>
      </td>
      <td className="px-1 py-2 text-center text-sky-600">✎</td>
      <td className={`px-1 py-2 text-center ${m.highAlert ? "text-amber-400" : "text-slate-300"}`}>
        {m.highAlert ? "★" : "☆"}
      </td>
      <td className="px-2 py-2">
        <span className="font-semibold text-slate-800">{m.name}</span>
        {m.highAlert && (
          <span className="ml-1.5 rounded bg-rose-600 px-1.5 py-0.5 text-[10px] font-semibold text-white">
            High alert
          </span>
        )}
      </td>
      <td className="px-2 py-2">{m.dose}</td>
      <td className="px-2 py-2 text-slate-600">{m.sig}</td>
      <td className="px-2 py-2">{m.refillsLeft ?? "—"}</td>
      <td className="px-2 py-2">{m.lastFilled}</td>
      <td className="px-2 py-2">{m.prescriber}</td>
      <td className="px-2 py-2">
        <span
          className={`rounded px-1.5 py-0.5 text-[10px] font-semibold ${
            m.status === "Active"
              ? "bg-emerald-100 text-emerald-700"
              : "bg-slate-200 text-slate-500"
          }`}
        >
          {m.status}
        </span>
      </td>
      <td className="px-2 py-2 text-center text-slate-400">🗑</td>
    </tr>
  );
}
