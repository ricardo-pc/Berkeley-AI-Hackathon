"use client";

import { useState } from "react";
import type { EncounterRow } from "../../_lib/ehr";
import { BadgeBar } from "../BadgeBar";
import { IconRail } from "../IconRail";

// Faithful recreation of the eClinicalWorks 11e "Encounters" (billing) screen,
// populated from the `messages` table (patient→provider relay requests). The
// filter/action chrome is illustrative; the table is live data.

export function EncountersScreen({ encounters }: { encounters: EncounterRow[] }) {
  const [selected, setSelected] = useState<string | null>(null);
  const [checked, setChecked] = useState<Set<string>>(() => new Set());

  const allChecked = encounters.length > 0 && encounters.every((e) => checked.has(e.id));
  const toggle = (id: string) =>
    setChecked((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  const toggleAll = () =>
    setChecked(allChecked ? new Set() : new Set(encounters.map((e) => e.id)));

  return (
    <div className="flex h-screen w-full select-none bg-slate-200 text-slate-800">
      <IconRail />
      <div className="flex min-w-0 flex-1 flex-col">
        <BadgeBar />

        {/* title bar */}
        <div className="flex flex-shrink-0 items-center gap-2 bg-gradient-to-b from-sky-500 to-sky-600 px-3 py-1.5 text-white">
          <span aria-hidden>🔒</span>
          <span className="text-sm font-semibold">Encounters ▾</span>
        </div>

        <FilterPanel />
        <ActionBar />

        {/* table */}
        <div className="min-h-0 flex-1 overflow-auto bg-white">
          <table className="w-full text-xs">
            <thead className="sticky top-0 z-10">
              <tr className="border-b border-slate-300 bg-gradient-to-b from-slate-100 to-slate-200 text-left text-slate-600">
                <th className="w-8 px-2 py-2 text-center">
                  <input type="checkbox" checked={allChecked} onChange={toggleAll} />
                </th>
                <th className="w-8 px-1 py-2 text-center">✓</th>
                <th className="px-3 py-2 font-semibold">Service Date</th>
                <th className="px-3 py-2 font-semibold">Provider</th>
                <th className="px-3 py-2 font-semibold">Resource</th>
                <th className="px-3 py-2 font-semibold">Patient</th>
                <th className="px-3 py-2 font-semibold">Primary Insurance</th>
              </tr>
            </thead>
            <tbody>
              {encounters.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-3 py-8 text-center text-slate-400">
                    No encounters found.
                  </td>
                </tr>
              ) : (
                encounters.map((e) => (
                  <tr
                    key={e.id}
                    onClick={() => setSelected(e.id)}
                    title={e.message}
                    className={`cursor-pointer border-b border-slate-100 ${
                      selected === e.id ? "bg-rose-100" : "hover:bg-sky-50"
                    }`}
                  >
                    <td className="px-2 py-2 text-center" onClick={(ev) => ev.stopPropagation()}>
                      <input
                        type="checkbox"
                        checked={checked.has(e.id)}
                        onChange={() => toggle(e.id)}
                      />
                    </td>
                    <td className="px-1 py-2 text-center text-emerald-600">
                      {e.delivered ? "✓" : ""}
                    </td>
                    <td className="px-3 py-2 text-slate-700">{e.serviceDate}</td>
                    <td className="px-3 py-2 text-slate-700">{e.provider}</td>
                    <td className="px-3 py-2 text-slate-600">{e.resource}</td>
                    <td className="px-3 py-2 font-semibold text-sky-800">{e.patient}</td>
                    <td className="px-3 py-2 text-slate-600">{e.insurance}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* footer */}
        <div className="flex flex-shrink-0 items-center justify-end gap-3 border-t border-slate-300 bg-slate-100 px-4 py-1.5 text-[11px] text-slate-600">
          <span>
            Total Encounters: <b>{encounters.length}</b>
          </span>
          <span className="text-slate-300">|</span>
          <button className="rounded border border-slate-300 bg-white px-2 py-0.5 hover:bg-slate-50">
            PREV
          </button>
          <span>
            Page <input readOnly value="1" className="w-7 rounded border border-slate-300 px-1 text-center" /> of 1
          </span>
          <button className="rounded border border-slate-300 bg-white px-2 py-0.5 hover:bg-slate-50">
            NEXT
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------- filter panel
function FilterPanel() {
  const inp =
    "rounded border border-slate-300 bg-white px-2 py-1 text-[11px] text-slate-700 focus:outline-none";
  return (
    <div className="flex flex-shrink-0 flex-wrap items-center gap-x-4 gap-y-2 border-b border-slate-300 bg-slate-50 px-3 py-2 text-[11px] text-slate-600">
      <label className="flex items-center gap-1">
        Provider(s) ▾
        <input type="checkbox" defaultChecked className="ml-1" /> All
        <input className={`${inp} w-36`} defaultValue="Lee, Sarah" />
        <button className={`${inp} px-2`}>…</button>
      </label>
      <label className="flex items-center gap-1">
        Facility ▾
        <input className={`${inp} w-44`} placeholder="" />
      </label>
      <label className="flex items-center gap-1">
        Service Date
        <input className={`${inp} w-24`} defaultValue="06/01/2026" />
        <span>to</span>
        <input className={`${inp} w-24`} defaultValue="06/30/2026" />
        <span aria-hidden>📅</span>
      </label>
      <label className="flex items-center gap-1">
        Insurance ▾
        <input className={`${inp} w-32`} placeholder="" />
        <button className={`${inp} px-2`}>Clr</button>
      </label>
      <label className="flex items-center gap-1">
        Select
        <select className={`${inp} w-48`} defaultValue="All Messages">
          <option>All Messages</option>
          <option>Undelivered</option>
          <option>Delivered</option>
        </select>
      </label>
      <label className="flex items-center gap-1">
        No of Days
        <select className={`${inp} w-16`} defaultValue="30">
          <option>30</option>
          <option>60</option>
          <option>90</option>
        </select>
      </label>
      <button className="ml-auto rounded bg-gradient-to-b from-sky-500 to-sky-600 px-3 py-1 text-[11px] font-semibold text-white hover:from-sky-600 hover:to-sky-700">
        ▽ Filter
      </button>
    </div>
  );
}

// ---------------------------------------------------------------- action bar
function ActionBar() {
  const btn =
    "rounded border border-slate-400 bg-gradient-to-b from-white to-slate-100 px-3 py-1 text-[11px] font-semibold text-slate-700 hover:from-slate-50 hover:to-slate-200";
  return (
    <div className="flex flex-shrink-0 items-center gap-2 border-b border-slate-300 bg-gradient-to-b from-sky-600 to-sky-700 px-3 py-1.5">
      <div className="flex">
        <button className={`${btn} rounded-r-none`}>Copy (F2)</button>
        <button className={`${btn} rounded-l-none border-l-0 px-1.5`}>▾</button>
      </div>
      <button className={btn}>Progress Notes (F3)</button>
      <button className={btn}>Claims IPE All (F4)</button>
      <button className={btn}>Claims IPE Selected (F6)</button>
    </div>
  );
}
