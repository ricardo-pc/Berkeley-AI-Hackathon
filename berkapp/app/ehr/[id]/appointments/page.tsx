"use client";

import { useState } from "react";
import { useActivePatient } from "../../../_components/PatientContext";
import {
  Button,
  Field,
  Input,
  Modal,
  Panel,
  Select,
  Stepper,
} from "../../../_components/ui";
import { openSlots, providers, visitTypes } from "../../../_lib/data";

const STEPS = ["Reason / type", "Provider", "Find a slot", "Confirm"];

export default function AppointmentsPage() {
  const patient = useActivePatient();
  const existing = patient.appointments[0];

  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState<"new" | "reschedule">("new");
  const [step, setStep] = useState(0);
  const [done, setDone] = useState(false);

  const [visitType, setVisitType] = useState(visitTypes[1]);
  const [provider, setProvider] = useState(providers[0].name);
  const [day, setDay] = useState<string | null>(null);
  const [slot, setSlot] = useState<string | null>(null);
  const [reason, setReason] = useState("");

  function start(m: "new" | "reschedule") {
    setMode(m);
    setOpen(true);
    setStep(0);
    setDone(false);
    setVisitType(visitTypes[1]);
    setProvider(providers[0].name);
    setDay(null);
    setSlot(null);
    setReason(m === "reschedule" ? "Patient requested earlier date" : "");
  }

  const canAdvance =
    (step !== 0 || reason.trim().length > 2) && (step !== 2 || (day && slot));

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-slate-700">Appointments</h1>
        <Button variant="primary" onClick={() => start("new")}>
          ＋ Schedule Appointment
        </Button>
      </div>

      <Panel title="Scheduled">
        {existing ? (
          <div className="flex items-center justify-between rounded border border-slate-200 bg-slate-50 p-3 text-xs">
            <div>
              <div className="font-semibold text-slate-700">
                {existing.date} · {existing.time}
              </div>
              <div className="text-slate-500">
                {existing.type} — {existing.provider}
              </div>
            </div>
            <div className="flex gap-2">
              <Button onClick={() => start("reschedule")}>Reschedule</Button>
              <Button variant="danger">Cancel</Button>
            </div>
          </div>
        ) : (
          <p className="text-xs text-slate-500">No scheduled appointments.</p>
        )}
        <p className="mt-3 text-[11px] text-slate-400">
          A &quot;can I move my appointment?&quot; voicemail means: open the
          calendar, match visit type and provider, hunt for an open slot that fits
          the patient&apos;s preference, rebook, and notify them.
        </p>
      </Panel>

      {open && !done && (
        <Modal
          title={mode === "reschedule" ? "Reschedule Appointment" : "Schedule Appointment"}
          onClose={() => setOpen(false)}
          width="max-w-2xl"
        >
          <Stepper steps={STEPS} current={step} />

          <div className="mb-3 rounded border border-slate-200 bg-slate-50 p-2 text-xs text-slate-600">
            {patient.name} · DOB {patient.dob} · {patient.insurance}
          </div>

          {step === 0 && (
            <div className="space-y-3">
              <Field label="Visit type" required>
                <Select value={visitType} onChange={(e) => setVisitType(e.target.value)}>
                  {visitTypes.map((v) => (
                    <option key={v}>{v}</option>
                  ))}
                </Select>
              </Field>
              <Field label="Reason for visit" required>
                <Input
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="e.g., INR recheck / follow-up"
                />
              </Field>
            </div>
          )}

          {step === 1 && (
            <div className="space-y-2">
              <Field label="Provider" required>
                <Select value={provider} onChange={(e) => setProvider(e.target.value)}>
                  {providers.map((p) => (
                    <option key={p.id}>
                      {p.name} — {p.specialty}
                    </option>
                  ))}
                </Select>
              </Field>
              <p className="text-[11px] text-slate-500">
                Check that the provider is in-network for the patient&apos;s plan
                and that the visit type matches their template.
              </p>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-3">
              <p className="text-xs text-slate-600">
                Open slots for <b>{provider}</b> — pick a day, then a time:
              </p>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                {Object.keys(openSlots).map((d) => (
                  <button
                    key={d}
                    onClick={() => {
                      setDay(d);
                      setSlot(null);
                    }}
                    className={`rounded border px-2 py-1.5 text-xs ${
                      day === d
                        ? "border-sky-600 bg-sky-50 font-semibold text-sky-800"
                        : "border-slate-300 bg-white text-slate-600 hover:bg-slate-50"
                    }`}
                  >
                    {d}
                  </button>
                ))}
              </div>
              {day && (
                <div className="flex flex-wrap gap-2 border-t border-slate-200 pt-3">
                  {openSlots[day].map((t) => (
                    <button
                      key={t}
                      onClick={() => setSlot(t)}
                      className={`rounded border px-3 py-1 text-xs ${
                        slot === t
                          ? "border-sky-600 bg-sky-600 font-semibold text-white"
                          : "border-slate-300 bg-white text-slate-600 hover:bg-slate-50"
                      }`}
                    >
                      {t}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {step === 3 && (
            <div className="space-y-3 text-xs text-slate-700">
              <div className="rounded border border-slate-200 bg-slate-50 p-3">
                <div>
                  <b>Type:</b> {visitType}
                </div>
                <div>
                  <b>Provider:</b> {provider}
                </div>
                <div>
                  <b>When:</b> {day} at {slot}
                </div>
                <div>
                  <b>Reason:</b> {reason}
                </div>
              </div>
              {mode === "reschedule" && existing && (
                <div className="rounded border border-amber-300 bg-amber-50 p-2 text-amber-800">
                  ⚠ This will cancel the existing {existing.date} appointment. The
                  patient must be notified of the change.
                </div>
              )}
              <label className="flex items-center gap-2">
                <input type="checkbox" /> Send appointment reminder to patient
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
                  disabled={!canAdvance}
                  onClick={() => setStep((s) => s + 1)}
                >
                  Next ›
                </Button>
              ) : (
                <Button variant="primary" onClick={() => setDone(true)}>
                  {mode === "reschedule" ? "Rebook" : "Book Appointment"}
                </Button>
              )}
            </div>
          </div>
        </Modal>
      )}

      {open && done && (
        <Modal title="Appointment booked" onClose={() => setOpen(false)}>
          <div className="space-y-3 text-center">
            <div className="text-4xl">✅</div>
            <p className="text-sm text-slate-700">
              {visitType.split("—")[0].trim()} booked for {day} at {slot} with{" "}
              {provider}.
            </p>
            <p className="text-xs text-slate-500">
              Now call the patient back to confirm — one more open task.
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
