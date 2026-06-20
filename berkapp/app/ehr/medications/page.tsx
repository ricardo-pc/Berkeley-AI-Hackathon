"use client";

import { useState } from "react";
import {
  Button,
  Field,
  Input,
  Modal,
  Panel,
  Select,
  Stepper,
} from "../../_components/ui";
import { type Medication, medications, pharmacies, patient } from "../../_lib/data";

const STEPS = [
  "Select Rx",
  "Verify patient",
  "Drug interactions",
  "Pharmacy",
  "Quantity & refills",
  "Review & sign",
];

export default function MedicationsPage() {
  const [active, setActive] = useState<Medication | null>(null);
  const [step, setStep] = useState(0);
  const [done, setDone] = useState(false);

  // form state collected across the wizard
  const [pharmacy, setPharmacy] = useState(pharmacies[0]);
  const [qty, setQty] = useState("30");
  const [refills, setRefills] = useState("1");
  const [ackInteraction, setAckInteraction] = useState(false);
  const [ackOverride, setAckOverride] = useState("");

  function startRefill(med: Medication) {
    setActive(med);
    setStep(0);
    setDone(false);
    setPharmacy(med.pharmacy.includes("Walgreens") ? pharmacies[0] : pharmacies[0]);
    setQty(med.qty.replace(/[^0-9]/g, "") || "30");
    setRefills("1");
    setAckInteraction(false);
    setAckOverride("");
  }

  function close() {
    setActive(null);
  }

  const isWarfarin = active?.id === "rx-warfarin";
  const canAdvance =
    step !== 2 || ackInteraction; // must acknowledge interactions to pass step 3
  const canSign = !isWarfarin || ackOverride.trim().length > 3;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-slate-700">Medications / Rx</h1>
        <div className="flex gap-2">
          <Button>＋ Add New Rx</Button>
          <Button>Reconcile</Button>
          <Button>Print Med List</Button>
        </div>
      </div>

      <Panel title="Active Medication List">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-slate-300 text-left text-slate-500">
              <th className="py-1.5 font-medium">Medication</th>
              <th className="py-1.5 font-medium">Sig (directions)</th>
              <th className="py-1.5 font-medium">Qty</th>
              <th className="py-1.5 font-medium">Refills</th>
              <th className="py-1.5 font-medium">Last filled</th>
              <th className="py-1.5 font-medium">Pharmacy</th>
              <th className="py-1.5 font-medium text-right">Action</th>
            </tr>
          </thead>
          <tbody>
            {medications.map((m) => (
              <tr key={m.id} className="border-b border-slate-100 align-top hover:bg-slate-50">
                <td className="py-2 font-semibold text-slate-700">
                  {m.name}
                  <div className="font-normal text-slate-400">{m.dose}</div>
                </td>
                <td className="py-2 text-slate-600">{m.sig}</td>
                <td className="py-2 text-slate-600">{m.qty}</td>
                <td className="py-2">
                  <span
                    className={
                      m.refillsLeft === 0
                        ? "font-semibold text-rose-600"
                        : "text-slate-600"
                    }
                  >
                    {m.refillsLeft}
                  </span>
                </td>
                <td className="py-2 text-slate-500">{m.lastFilled}</td>
                <td className="py-2 text-slate-500">{m.pharmacy}</td>
                <td className="py-2 text-right">
                  <Button variant="primary" onClick={() => startRefill(m)}>
                    Refill
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="mt-3 text-[11px] text-slate-400">
          To refill a single prescription a staff member must open the order,
          re-verify the patient and insurance, clear interaction warnings, choose
          the pharmacy, set quantity/refills, and sign — for each call.
        </p>
      </Panel>

      {active && !done && (
        <Modal title={`Refill — ${active.name}`} onClose={close} width="max-w-2xl">
          <Stepper steps={STEPS} current={step} />

          {step === 0 && (
            <div className="space-y-3 text-xs text-slate-700">
              <p>Confirm the prescription to refill:</p>
              <div className="rounded border border-slate-200 bg-slate-50 p-3">
                <div className="font-semibold">
                  {active.name} — {active.dose}
                </div>
                <div className="text-slate-500">{active.sig}</div>
                <div className="mt-1 text-slate-500">
                  Prescriber: {active.prescriber} · Refills left:{" "}
                  {active.refillsLeft}
                </div>
              </div>
              {active.refillsLeft === 0 && (
                <div className="rounded border border-amber-300 bg-amber-50 p-2 text-amber-800">
                  ⚠ No refills remaining — prescriber authorization required before
                  this can be sent.
                </div>
              )}
            </div>
          )}

          {step === 1 && (
            <div className="space-y-2 text-xs text-slate-700">
              <p>Verify patient demographics & active coverage:</p>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <b>Name:</b> {patient.name}
                </div>
                <div>
                  <b>DOB:</b> {patient.dob}
                </div>
                <div>
                  <b>MRN:</b> {patient.mrn}
                </div>
                <div>
                  <b>Insurance:</b> {patient.insurance}
                </div>
                <div>
                  <b>Member ID:</b> {patient.insuranceId}
                </div>
                <div>
                  <b>Phone:</b> {patient.phone}
                </div>
              </div>
              <label className="mt-2 flex items-center gap-2">
                <input type="checkbox" defaultChecked /> Eligibility verified
                (real-time 270/271)
              </label>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-3 text-xs">
              <p className="text-slate-700">Interaction & allergy screening:</p>
              {isWarfarin ? (
                <div className="space-y-2">
                  <div className="rounded border border-rose-300 bg-rose-50 p-3 text-rose-800">
                    <div className="font-bold">⚠ SEVERE INTERACTION — Warfarin</div>
                    <ul className="ml-4 mt-1 list-disc">
                      <li>
                        Warfarin + Atorvastatin: increased bleeding risk — monitor
                        INR.
                      </li>
                      <li>
                        Narrow therapeutic index drug — dose must reflect latest
                        INR (2.4 on 05/22/2026).
                      </li>
                    </ul>
                  </div>
                  <div className="rounded border border-amber-300 bg-amber-50 p-2 text-amber-800">
                    ⚠ Allergy cross-check: Penicillin, Sulfa — no conflict with this
                    order.
                  </div>
                </div>
              ) : (
                <div className="rounded border border-amber-300 bg-amber-50 p-2 text-amber-800">
                  ⚠ Minor: take with food. No severe interactions detected.
                </div>
              )}
              <label className="flex items-center gap-2 text-slate-700">
                <input
                  type="checkbox"
                  checked={ackInteraction}
                  onChange={(e) => setAckInteraction(e.target.checked)}
                />
                I have reviewed and acknowledge the above warning(s).
              </label>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-3">
              <Field label="Dispensing pharmacy" required>
                <Select
                  value={pharmacy}
                  onChange={(e) => setPharmacy(e.target.value)}
                >
                  {pharmacies.map((p) => (
                    <option key={p}>{p}</option>
                  ))}
                </Select>
              </Field>
              <p className="text-[11px] text-slate-500">
                Confirm the patient still uses this pharmacy — patients frequently
                change without telling the office.
              </p>
            </div>
          )}

          {step === 4 && (
            <div className="grid grid-cols-2 gap-3">
              <Field label="Quantity" required>
                <Input value={qty} onChange={(e) => setQty(e.target.value)} />
              </Field>
              <Field label="Refills authorized" required>
                <Select value={refills} onChange={(e) => setRefills(e.target.value)}>
                  {["0", "1", "2", "3", "5", "11"].map((n) => (
                    <option key={n}>{n}</option>
                  ))}
                </Select>
              </Field>
              <Field label="Days supply">
                <Input defaultValue="30" />
              </Field>
              <Field label="Substitution">
                <Select defaultValue="Allowed">
                  <option>Allowed</option>
                  <option>Dispense as written</option>
                </Select>
              </Field>
            </div>
          )}

          {step === 5 && (
            <div className="space-y-3 text-xs text-slate-700">
              <div className="rounded border border-slate-200 bg-slate-50 p-3">
                <div className="font-semibold">{active.name} — {active.dose}</div>
                <div>Qty {qty} · {refills} refill(s)</div>
                <div>Pharmacy: {pharmacy}</div>
                <div>Prescriber: {active.prescriber}</div>
              </div>
              {isWarfarin && (
                <Field label="Prescriber override reason (no refills remaining)" required>
                  <Input
                    value={ackOverride}
                    onChange={(e) => setAckOverride(e.target.value)}
                    placeholder="e.g., Verbal auth from Dr. Okafor 06/20"
                  />
                </Field>
              )}
              <label className="flex items-center gap-2">
                <input type="checkbox" /> Electronically sign and transmit (EPCS)
              </label>
            </div>
          )}

          <div className="mt-5 flex items-center justify-between border-t border-slate-200 pt-3">
            <Button onClick={close} variant="ghost">
              Cancel
            </Button>
            <div className="flex gap-2">
              {step > 0 && (
                <Button onClick={() => setStep((s) => s - 1)}>‹ Back</Button>
              )}
              {step < STEPS.length - 1 ? (
                <Button
                  variant="primary"
                  disabled={!canAdvance}
                  onClick={() => setStep((s) => s + 1)}
                >
                  Next ›
                </Button>
              ) : (
                <Button
                  variant="primary"
                  disabled={!canSign}
                  onClick={() => setDone(true)}
                >
                  Sign & Send to Pharmacy
                </Button>
              )}
            </div>
          </div>
        </Modal>
      )}

      {active && done && (
        <Modal title="Prescription transmitted" onClose={close}>
          <div className="space-y-3 text-center">
            <div className="text-4xl">✅</div>
            <p className="text-sm text-slate-700">
              <b>{active.name}</b> sent to {pharmacy.split("—")[0].trim()}.
            </p>
            <p className="text-xs text-slate-500">
              That was one prescription for one patient. There are dozens more
              voicemails in the queue.
            </p>
            <Button variant="primary" onClick={close}>
              Done
            </Button>
          </div>
        </Modal>
      )}
    </div>
  );
}
