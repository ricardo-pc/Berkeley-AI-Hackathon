"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useActivePatient } from "./PatientContext";

const topMenus = [
  "File",
  "Patient",
  "Schedule",
  "Encounters",
  "Messages",
  "Billing",
  "Reports",
  "Tools",
  "Help",
];

const navItems = [
  { seg: "", label: "Patient Hub", icon: "🏠" },
  { seg: "/medications", label: "Medications / Rx", icon: "💊" },
  { seg: "/coumadin", label: "Coumadin / INR", icon: "🩸" },
  { seg: "/messages", label: "Telephone Encounters", icon: "📞" },
  { seg: "/appointments", label: "Appointments", icon: "📅" },
  { seg: "#", label: "Progress Notes", icon: "📝" },
  { seg: "#", label: "Labs / Diagnostics", icon: "🧪" },
  { seg: "#", label: "Documents", icon: "📁" },
  { seg: "#", label: "Referrals", icon: "↗️" },
  { seg: "#", label: "Immunizations", icon: "💉" },
  { seg: "#", label: "Account Inquiry", icon: "💳" },
];

export function TopBar() {
  const router = useRouter();
  return (
    <header className="flex-shrink-0">
      {/* brand + menu row */}
      <div className="flex items-center justify-between bg-gradient-to-b from-teal-700 to-teal-900 px-3 text-white">
        <div className="flex items-center gap-4">
          <span className="py-1.5 text-sm font-bold tracking-tight">
            eClinical<span className="text-teal-300">Works</span>
            <sup className="ml-0.5 text-[8px]">®</sup>
          </span>
          <nav className="hidden gap-1 md:flex">
            {topMenus.map((m) => (
              <button key={m} className="rounded px-2 py-1 text-xs hover:bg-white/15">
                {m}
              </button>
            ))}
          </nav>
        </div>
        <div className="flex items-center gap-3 text-xs">
          <span className="hidden sm:inline">Front Desk — D. Alvarez</span>
          <span className="hidden text-teal-300 sm:inline">|</span>
          <span className="hidden sm:inline">Berkeley Internal Med Assoc.</span>
          <button
            onClick={() => router.push("/")}
            className="rounded bg-white/15 px-2 py-1 hover:bg-white/25"
          >
            Log off
          </button>
        </div>
      </div>
      {/* icon toolbar row */}
      <div className="flex items-center gap-1 border-b border-slate-300 bg-gradient-to-b from-slate-50 to-slate-200 px-3 py-1">
        <Link
          href="/ehr"
          className="rounded border border-slate-300 bg-white px-2 py-1 text-[11px] font-semibold text-sky-700 hover:bg-sky-50"
        >
          ▤ Patient List
        </Link>
        {["New Tel Encounter", "Rx", "Labs", "Schedule", "Hub", "Messages", "Print"].map(
          (t) => (
            <button
              key={t}
              className="rounded border border-transparent px-2 py-1 text-[11px] text-slate-600 hover:border-slate-300 hover:bg-white"
            >
              {t}
            </button>
          ),
        )}
        <div className="ml-auto flex items-center gap-1">
          <input
            placeholder="Search patient (name / DOB / MRN)…"
            className="w-56 rounded border border-slate-300 px-2 py-1 text-[11px] focus:outline-none"
          />
          <button className="rounded border border-slate-300 bg-white px-2 py-1 text-[11px] text-slate-600">
            🔍
          </button>
        </div>
      </div>
    </header>
  );
}

export function PatientBanner() {
  const patient = useActivePatient();
  return (
    <div className="flex flex-shrink-0 flex-wrap items-stretch gap-px border-b border-slate-300 bg-slate-200">
      <div className="flex items-center gap-3 bg-white px-4 py-2">
        <div className="flex h-12 w-12 items-center justify-center rounded bg-gradient-to-br from-slate-500 to-slate-700 text-base font-bold text-white">
          {patient.photoInitials}
        </div>
        <div>
          <div className="text-base font-bold leading-tight text-slate-800">
            {patient.name}{" "}
            {patient.preferredName && (
              <span className="text-xs font-normal text-slate-500">
                ({patient.preferredName})
              </span>
            )}
          </div>
          <div className="text-[11px] text-slate-600">
            {patient.sex} · {patient.age} yrs · DOB {patient.dob}
          </div>
        </div>
      </div>
      <div className="flex flex-1 flex-wrap items-center gap-x-6 gap-y-1 bg-white px-4 py-2 text-[11px] text-slate-600">
        <span>
          <b className="text-slate-500">MRN:</b> {patient.mrn}
        </span>
        <span>
          <b className="text-slate-500">PCP:</b> {patient.pcp}
        </span>
        <span>
          <b className="text-slate-500">Phone:</b> {patient.phone}
        </span>
        <span>
          <b className="text-slate-500">Insurance:</b> {patient.insurance}
        </span>
        <span>
          <b className="text-slate-500">Balance:</b> {patient.balance}
        </span>
      </div>
      <div className="flex items-center bg-rose-50 px-4 py-2">
        <span className="text-[11px] font-semibold text-rose-700">
          ⚠ Allergies:{" "}
          {patient.allergies.length
            ? patient.allergies.map((a) => a.substance).join(", ")
            : "No Known Drug Allergies"}
        </span>
      </div>
    </div>
  );
}

export function LeftNav() {
  const pathname = usePathname();
  const patient = useActivePatient();
  const base = `/ehr/${patient.id}`;
  return (
    <nav className="w-52 flex-shrink-0 overflow-y-auto border-r border-slate-300 bg-slate-100">
      <div className="bg-gradient-to-b from-slate-200 to-slate-300 px-3 py-1.5 text-[11px] font-bold uppercase tracking-wide text-slate-600">
        Patient Chart
      </div>
      <ul>
        {navItems.map((item) => {
          const href = item.seg === "#" ? "#" : `${base}${item.seg}`;
          const active = pathname === href;
          const disabled = item.seg === "#";
          return (
            <li key={item.label}>
              <Link
                href={href}
                className={`flex items-center gap-2 border-b border-slate-200 px-3 py-2 text-xs ${
                  active
                    ? "border-l-4 border-l-sky-600 bg-white font-semibold text-sky-800"
                    : disabled
                      ? "text-slate-400"
                      : "text-slate-700 hover:bg-white"
                }`}
              >
                <span aria-hidden>{item.icon}</span>
                {item.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
