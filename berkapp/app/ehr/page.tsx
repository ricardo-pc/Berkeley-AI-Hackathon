import Link from "next/link";
import { Panel } from "../_components/ui";
import {
  allergies,
  inrHistory,
  medications,
  problems,
  upcomingAppointments,
} from "../_lib/data";

export default function PatientHub() {
  const latestInr = inrHistory[0];
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-slate-700">Patient Hub</h1>
        <span className="text-xs text-slate-500">
          Last reviewed 06/20/2026 · No outstanding alerts acknowledged
        </span>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Panel title="Active Problems">
          <ul className="space-y-1 text-xs">
            {problems.map((p) => (
              <li key={p.code} className="flex justify-between border-b border-slate-100 pb-1">
                <span className="text-slate-700">{p.description}</span>
                <span className="text-slate-400">
                  {p.code} · {p.since}
                </span>
              </li>
            ))}
          </ul>
        </Panel>

        <Panel title="Allergies / Intolerances">
          <ul className="space-y-1 text-xs">
            {allergies.map((a) => (
              <li key={a.substance} className="flex justify-between border-b border-slate-100 pb-1">
                <span className="font-semibold text-rose-700">{a.substance}</span>
                <span className="text-slate-500">
                  {a.reaction} · {a.severity}
                </span>
              </li>
            ))}
          </ul>
        </Panel>

        <Panel title="Anticoagulation Snapshot">
          <div className="text-xs text-slate-700">
            <div className="mb-2 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-slate-800">{latestInr.inr}</span>
              <span className="text-slate-500">latest INR ({latestInr.date})</span>
            </div>
            <div>Target range: 2.0 – 3.0</div>
            <div>Current dose: {latestInr.dose}</div>
            <Link
              href="/ehr/coumadin"
              className="mt-2 inline-block text-sky-700 underline"
            >
              Open Coumadin flowsheet →
            </Link>
          </div>
        </Panel>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Panel
          title="Current Medications"
          right={
            <Link href="/ehr/medications" className="text-[11px] text-sky-700 underline">
              Manage / Refill
            </Link>
          }
        >
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-slate-200 text-left text-slate-500">
                <th className="py-1 font-medium">Medication</th>
                <th className="py-1 font-medium">Refills</th>
                <th className="py-1 font-medium">Last filled</th>
              </tr>
            </thead>
            <tbody>
              {medications.map((m) => (
                <tr key={m.id} className="border-b border-slate-100">
                  <td className="py-1 text-slate-700">
                    {m.name} <span className="text-slate-400">{m.dose}</span>
                  </td>
                  <td className="py-1">
                    <span
                      className={
                        m.refillsLeft === 0 ? "font-semibold text-rose-600" : "text-slate-600"
                      }
                    >
                      {m.refillsLeft}
                    </span>
                  </td>
                  <td className="py-1 text-slate-500">{m.lastFilled}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>

        <Panel
          title="Upcoming Appointments"
          right={
            <Link href="/ehr/appointments" className="text-[11px] text-sky-700 underline">
              Schedule
            </Link>
          }
        >
          {upcomingAppointments.length === 0 ? (
            <p className="text-xs text-slate-500">No upcoming appointments.</p>
          ) : (
            <ul className="space-y-2 text-xs">
              {upcomingAppointments.map((a) => (
                <li key={a.id} className="border-b border-slate-100 pb-2">
                  <div className="font-semibold text-slate-700">
                    {a.date} · {a.time}
                  </div>
                  <div className="text-slate-500">
                    {a.type} — {a.provider}
                  </div>
                  <span className="mt-1 inline-block rounded bg-sky-100 px-1.5 py-0.5 text-[10px] font-semibold text-sky-700">
                    {a.status}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Panel>
      </div>

      <Panel title="Front-desk note">
        <p className="text-xs text-slate-500">
          This is the chart a front-desk worker lands in for{" "}
          <b>every single voicemail</b>. A refill, a reschedule, or a message to
          the provider each means leaving this screen, navigating tabs, and
          re-entering data by hand. Use the left nav to walk through what that
          takes today.
        </p>
      </Panel>
    </div>
  );
}
