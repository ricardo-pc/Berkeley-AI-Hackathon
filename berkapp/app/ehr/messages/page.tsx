"use client";

import { useState } from "react";
import {
  Button,
  Field,
  Input,
  Modal,
  Panel,
  Select,
  Textarea,
} from "../../_components/ui";
import { patient, providers } from "../../_lib/data";

type Encounter = {
  id: string;
  date: string;
  subject: string;
  routedTo: string;
  priority: string;
  status: "Open" | "Closed";
};

const seedEncounters: Encounter[] = [
  {
    id: "te-1001",
    date: "06/18/2026",
    subject: "Question about metformin GI side effects",
    routedTo: "Dr. A. Okafor, MD",
    priority: "Routine",
    status: "Closed",
  },
  {
    id: "te-1000",
    date: "06/12/2026",
    subject: "Requesting copy of lab results",
    routedTo: "Front Desk",
    priority: "Low",
    status: "Closed",
  },
];

export default function MessagesPage() {
  const [open, setOpen] = useState(false);
  const [done, setDone] = useState(false);
  const [encounters, setEncounters] = useState(seedEncounters);

  const [subject, setSubject] = useState("");
  const [routedTo, setRoutedTo] = useState(providers[0].name);
  const [priority, setPriority] = useState("Routine");
  const [body, setBody] = useState("");
  const [callback, setCallback] = useState(patient.phone);

  function start() {
    setOpen(true);
    setDone(false);
    setSubject("");
    setRoutedTo(providers[0].name);
    setPriority("Routine");
    setBody("");
    setCallback(patient.phone);
  }

  function save() {
    setEncounters((prev) => [
      {
        id: `te-${1002 + prev.length}`,
        date: "06/20/2026",
        subject: subject || "(no subject)",
        routedTo,
        priority,
        status: "Open",
      },
      ...prev,
    ]);
    setDone(true);
  }

  const canSave = subject.trim().length > 2 && body.trim().length > 2;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-slate-700">
          Telephone Encounters
        </h1>
        <Button variant="primary" onClick={start}>
          ＋ New Telephone Encounter
        </Button>
      </div>

      <Panel title="Encounter History">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-slate-300 text-left text-slate-500">
              <th className="py-1.5 font-medium">ID</th>
              <th className="py-1.5 font-medium">Date</th>
              <th className="py-1.5 font-medium">Subject</th>
              <th className="py-1.5 font-medium">Routed to</th>
              <th className="py-1.5 font-medium">Priority</th>
              <th className="py-1.5 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {encounters.map((e) => (
              <tr key={e.id} className="border-b border-slate-100 hover:bg-slate-50">
                <td className="py-1.5 text-slate-400">{e.id}</td>
                <td className="py-1.5 text-slate-600">{e.date}</td>
                <td className="py-1.5 text-slate-700">{e.subject}</td>
                <td className="py-1.5 text-slate-600">{e.routedTo}</td>
                <td className="py-1.5 text-slate-600">{e.priority}</td>
                <td className="py-1.5">
                  <span
                    className={`rounded px-1.5 py-0.5 text-[10px] font-semibold ${
                      e.status === "Open"
                        ? "bg-amber-100 text-amber-700"
                        : "bg-slate-100 text-slate-500"
                    }`}
                  >
                    {e.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="mt-3 text-[11px] text-slate-400">
          Every &quot;please tell the doctor…&quot; voicemail becomes a hand-typed
          encounter: transcribe the message, pick the right provider, set
          priority, and route it — then someone has to close the loop.
        </p>
      </Panel>

      {open && !done && (
        <Modal title="New Telephone Encounter" onClose={() => setOpen(false)} width="max-w-2xl">
          <div className="space-y-3">
            <div className="rounded border border-slate-200 bg-slate-50 p-2 text-xs text-slate-600">
              Patient: <b>{patient.name}</b> · DOB {patient.dob} · MRN {patient.mrn}
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Callback number" required>
                <Input value={callback} onChange={(e) => setCallback(e.target.value)} />
              </Field>
              <Field label="Caller">
                <Select defaultValue="Patient">
                  <option>Patient</option>
                  <option>Spouse / caregiver</option>
                  <option>Pharmacy</option>
                </Select>
              </Field>
            </div>
            <Field label="Subject" required>
              <Input
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="e.g., Message for Dr. Okafor — not feeling well"
              />
            </Field>
            <Field label="Message / transcription" required>
              <Textarea
                value={body}
                onChange={(e) => setBody(e.target.value)}
                placeholder="Type out exactly what the patient said in the voicemail…"
              />
            </Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Route to" required>
                <Select value={routedTo} onChange={(e) => setRoutedTo(e.target.value)}>
                  {providers.map((p) => (
                    <option key={p.id}>{p.name}</option>
                  ))}
                  <option>Front Desk</option>
                </Select>
              </Field>
              <Field label="Priority" required>
                <Select value={priority} onChange={(e) => setPriority(e.target.value)}>
                  {["Low", "Routine", "High", "Urgent"].map((p) => (
                    <option key={p}>{p}</option>
                  ))}
                </Select>
              </Field>
            </div>
          </div>

          <div className="mt-5 flex items-center justify-between border-t border-slate-200 pt-3">
            <Button variant="ghost" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" disabled={!canSave} onClick={save}>
              Save & Route Encounter
            </Button>
          </div>
        </Modal>
      )}

      {open && done && (
        <Modal title="Encounter routed" onClose={() => setOpen(false)}>
          <div className="space-y-3 text-center">
            <div className="text-4xl">✅</div>
            <p className="text-sm text-slate-700">
              Encounter routed to {routedTo} ({priority}).
            </p>
            <p className="text-xs text-slate-500">
              It now sits in their inbox until someone reads it and acts — the loop
              isn&apos;t closed yet.
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
