"use client";

import { useMemo, useState } from "react";
import {
  Button,
  Field,
  Input,
  Modal,
  Panel,
  Select,
  Stepper,
} from "../../_components/ui";
import { inrHistory } from "../../_lib/data";

const STEPS = ["Enter INR", "Protocol guidance", "Adjust dose", "Schedule next", "Sign"];

// Very rough Coumadin nomogram for the demo — illustrative only.
function recommend(inr: number): { action: string; tone: "ok" | "warn" | "danger" } {
  if (inr < 1.5) return { action: "Sub-therapeutic. Increase weekly dose 10–15%, recheck in 1 week.", tone: "warn" };
  if (inr < 2.0) return { action: "Slightly low. Increase weekly dose 5–10%, recheck in 1–2 weeks.", tone: "warn" };
  if (inr <= 3.0) return { action: "In range. Continue current dose, recheck in 4 weeks.", tone: "ok" };
  if (inr <= 3.9) return { action: "Slightly high. Decrease weekly dose 5–10%, recheck in 1 week.", tone: "warn" };
  if (inr <= 4.9) return { action: "High. Hold 1 dose, decrease weekly dose 10%, recheck in 3–5 days.", tone: "danger" };
  return { action: "Critical. Hold 1–2 doses, consider vitamin K, recheck in 1–2 days. Notify provider.", tone: "danger" };
}

export default function CoumadinPage() {
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState(0);
  const [done, setDone] = useState(false);

  const [newInr, setNewInr] = useState("");
  const [newDose, setNewDose] = useState("35 mg/wk");
  const [recheck, setRecheck] = useState("4 weeks");
  const [notify, setNotify] = useState(false);

  const inrNum = parseFloat(newInr);
  const rec = useMemo(
    () => (isNaN(inrNum) ? null : recommend(inrNum)),
    [inrNum],
  );

  function start() {
    setOpen(true);
    setStep(0);
    setDone(false);
    setNewInr("");
    setNewDose("35 mg/wk");
    setRecheck("4 weeks");
    setNotify(false);
  }

  const toneCls = {
    ok: "border-emerald-300 bg-emerald-50 text-emerald-800",
    warn: "border-amber-300 bg-amber-50 text-amber-800",
    danger: "border-rose-300 bg-rose-50 text-rose-800",
  } as const;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-slate-700">
          Coumadin / Anticoagulation Management
        </h1>
        <Button variant="primary" onClick={start}>
          ＋ Record INR Result
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Panel title="Therapy">
          <dl className="space-y-1 text-xs text-slate-700">
            <div className="flex justify-between">
              <dt className="text-slate-500">Indication</dt>
              <dd>Atrial fibrillation</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Target INR</dt>
              <dd>2.0 – 3.0</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Current dose</dt>
              <dd>{inrHistory[0].dose}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Managed by</dt>
              <dd>Anticoag Clinic (RN)</dd>
            </div>
          </dl>
        </Panel>
        <Panel title="Latest INR" className="lg:col-span-2">
          <div className="flex items-end gap-6">
            <div>
              <div className="text-4xl font-bold text-slate-800">
                {inrHistory[0].inr}
              </div>
              <div className="text-xs text-slate-500">{inrHistory[0].date}</div>
            </div>
            <div className="flex-1 text-xs text-slate-600">
              {inrHistory[0].action}. Next routine draw due 06/19/2026 — call from
              patient indicates they missed it.
            </div>
          </div>
        </Panel>
      </div>

      <Panel title="INR Flowsheet">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-slate-300 text-left text-slate-500">
              <th className="py-1.5 font-medium">Date</th>
              <th className="py-1.5 font-medium">INR</th>
              <th className="py-1.5 font-medium">In range?</th>
              <th className="py-1.5 font-medium">Weekly dose</th>
              <th className="py-1.5 font-medium">Action taken</th>
            </tr>
          </thead>
          <tbody>
            {inrHistory.map((r) => {
              const inRange = r.inr >= 2.0 && r.inr <= 3.0;
              return (
                <tr key={r.date} className="border-b border-slate-100">
                  <td className="py-1.5 text-slate-600">{r.date}</td>
                  <td className="py-1.5 font-semibold text-slate-800">{r.inr}</td>
                  <td className="py-1.5">
                    <span
                      className={`rounded px-1.5 py-0.5 text-[10px] font-semibold ${
                        inRange
                          ? "bg-emerald-100 text-emerald-700"
                          : "bg-rose-100 text-rose-700"
                      }`}
                    >
                      {inRange ? "In range" : "Out of range"}
                    </span>
                  </td>
                  <td className="py-1.5 text-slate-600">{r.dose}</td>
                  <td className="py-1.5 text-slate-600">{r.action}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </Panel>

      {open && !done && (
        <Modal title="Record INR & Adjust Coumadin" onClose={() => setOpen(false)} width="max-w-2xl">
          <Stepper steps={STEPS} current={step} />

          {step === 0 && (
            <div className="grid grid-cols-2 gap-3">
              <Field label="INR value" required>
                <Input
                  value={newInr}
                  onChange={(e) => setNewInr(e.target.value)}
                  placeholder="e.g., 2.4"
                  inputMode="decimal"
                />
              </Field>
              <Field label="Draw date" required>
                <Input type="date" defaultValue="2026-06-20" />
              </Field>
              <Field label="Source">
                <Select defaultValue="POC fingerstick">
                  <option>POC fingerstick</option>
                  <option>Venous lab draw</option>
                  <option>Patient home monitor</option>
                </Select>
              </Field>
            </div>
          )}

          {step === 1 && (
            <div className="space-y-3 text-xs">
              {rec ? (
                <div className={`rounded border p-3 ${toneCls[rec.tone]}`}>
                  <div className="font-bold">INR {newInr} — protocol guidance</div>
                  <p className="mt-1">{rec.action}</p>
                </div>
              ) : (
                <p className="text-slate-500">Enter an INR value first.</p>
              )}
              <p className="text-[11px] text-slate-500">
                Nomogram is decision support only. The RN must still translate this
                into an exact weekly dose and recheck interval below.
              </p>
            </div>
          )}

          {step === 2 && (
            <div className="grid grid-cols-2 gap-3">
              <Field label="New weekly dose" required>
                <Input value={newDose} onChange={(e) => setNewDose(e.target.value)} />
              </Field>
              <Field label="Hold doses?">
                <Select defaultValue="None">
                  <option>None</option>
                  <option>Hold 1 dose</option>
                  <option>Hold 2 doses</option>
                </Select>
              </Field>
              <div className="col-span-2 rounded border border-slate-200 bg-slate-50 p-2 text-[11px] text-slate-600">
                Daily breakdown must be communicated to the patient by phone and
                documented — e.g., 5 mg M/W/F, 2.5 mg other days.
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-3">
              <Field label="Recheck interval" required>
                <Select value={recheck} onChange={(e) => setRecheck(e.target.value)}>
                  {["3 days", "1 week", "2 weeks", "4 weeks"].map((o) => (
                    <option key={o}>{o}</option>
                  ))}
                </Select>
              </Field>
              <label className="flex items-center gap-2 text-xs text-slate-700">
                <input
                  type="checkbox"
                  checked={notify}
                  onChange={(e) => setNotify(e.target.checked)}
                />
                Notify supervising provider (required if out of range)
              </label>
              <p className="text-[11px] text-slate-500">
                A lab-only INR appointment must be created separately on the
                schedule — see Appointments tab.
              </p>
            </div>
          )}

          {step === 4 && (
            <div className="space-y-3 text-xs text-slate-700">
              <div className="rounded border border-slate-200 bg-slate-50 p-3">
                <div>INR recorded: <b>{newInr || "—"}</b></div>
                <div>New weekly dose: <b>{newDose}</b></div>
                <div>Recheck: <b>{recheck}</b></div>
                <div>Provider notified: <b>{notify ? "Yes" : "No"}</b></div>
              </div>
              <label className="flex items-center gap-2">
                <input type="checkbox" /> Sign flowsheet entry & generate patient
                call note
              </label>
            </div>
          )}

          <div className="mt-5 flex items-center justify-between border-t border-slate-200 pt-3">
            <Button variant="ghost" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <div className="flex gap-2">
              {step > 0 && <Button onClick={() => setStep((s) => s - 1)}>‹ Back</Button>}
              {step < STEPS.length - 1 ? (
                <Button
                  variant="primary"
                  disabled={step === 0 && isNaN(inrNum)}
                  onClick={() => setStep((s) => s + 1)}
                >
                  Next ›
                </Button>
              ) : (
                <Button variant="primary" onClick={() => setDone(true)}>
                  Sign Entry
                </Button>
              )}
            </div>
          </div>
        </Modal>
      )}

      {open && done && (
        <Modal title="INR documented" onClose={() => setOpen(false)}>
          <div className="space-y-3 text-center">
            <div className="text-4xl">✅</div>
            <p className="text-sm text-slate-700">
              INR {newInr} recorded, dose set to {newDose}, recheck in {recheck}.
            </p>
            <p className="text-xs text-slate-500">
              Now the patient still has to be called back with their exact daily
              schedule — another task for the queue.
            </p>
            <Button variant="primary" onClick={() => setOpen(false)}>
              Done
            </Button>
          </div>
        </Modal>
      )}
    </div>
  );
}
