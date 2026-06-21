"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import type {
  DaySchedule,
  ScheduleAppointment,
  ScheduleProvider,
} from "../../_lib/ehr";
import { BadgeBar } from "../BadgeBar";
import { IconRail } from "../IconRail";

// Faithful-as-possible recreation of the eClinicalWorks 11e "Office Visits"
// resource-scheduler screen: far-left icon rail, dark badge bar, day toolbar,
// mini-calendar + provider list, and a column-per-provider 15-minute grid.

// ---- grid geometry ----
const START_MIN = 7 * 60; // 7:00 AM
const END_MIN = 19 * 60; // 7:00 PM
const SLOT = 30; // 30-minute intervals
const ROW_H = 28; // px per 30-minute slot
const ROWS = (END_MIN - START_MIN) / SLOT;
const BODY_H = ROWS * ROW_H;
const SLOTS_PER_HOUR = 60 / SLOT;

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];
const DOW = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];

// ---- date helpers (UTC, to match server-side day math) ----
function isoToUtc(iso: string): Date {
  return new Date(`${iso}T00:00:00Z`);
}
function utcToIso(d: Date): string {
  return d.toISOString().slice(0, 10);
}
function addDays(iso: string, n: number): string {
  const d = isoToUtc(iso);
  d.setUTCDate(d.getUTCDate() + n);
  return utcToIso(d);
}
function longDate(iso: string): string {
  const d = isoToUtc(iso);
  return `${MONTHS[d.getUTCMonth()]} ${d.getUTCDate()}, ${d.getUTCFullYear()}`;
}
function timeLabel(min: number): string {
  let h = Math.floor(min / 60);
  const m = min % 60;
  const ampm = h >= 12 ? "PM" : "AM";
  h = h % 12 || 12;
  return `${h}:${String(m).padStart(2, "0")} ${ampm}`;
}

export function ScheduleScreen({
  date,
  today,
  schedule,
}: {
  date: string;
  today: string;
  schedule: DaySchedule;
}) {
  const router = useRouter();
  const go = (iso: string) => router.push(`/schedule?date=${iso}`);

  const [visible, setVisible] = useState<Set<string>>(
    () => new Set(schedule.providers.map((p) => p.id)),
  );
  const toggle = (id: string) =>
    setVisible((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });

  const columns = schedule.providers.filter((p) => visible.has(p.id));

  return (
    <div className="flex h-screen w-full select-none bg-slate-200 text-slate-800">
      <IconRail />

      <div className="flex min-w-0 flex-1 flex-col">
        <BadgeBar />
        <DayToolbar date={date} today={today} onNavigate={go} />

        <div className="flex min-h-0 flex-1">
          <SidePanel
            date={date}
            today={today}
            providers={schedule.providers}
            visible={visible}
            onToggle={toggle}
            onPickDay={go}
          />
          <Grid date={date} columns={columns} appointments={schedule.appointments} />
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------- day toolbar
function DayToolbar({
  date,
  today,
  onNavigate,
}: {
  date: string;
  today: string;
  onNavigate: (iso: string) => void;
}) {
  const tBtn =
    "flex items-center gap-1 rounded border border-slate-300 bg-white px-2 py-1 text-[11px] text-slate-600 hover:bg-slate-50";
  return (
    <div className="flex flex-shrink-0 items-center gap-2 border-b border-slate-300 bg-gradient-to-b from-slate-100 to-slate-200 px-2 py-1.5">
      <button onClick={() => onNavigate(addDays(date, -1))} className={tBtn} aria-label="Previous day">‹</button>
      <span className={tBtn}>1 Day ▾</span>
      <span className={tBtn}>15 ▾</span>
      <button onClick={() => onNavigate(date)} className={tBtn} aria-label="Refresh">⟳</button>
      <span className={tBtn} aria-hidden>📅</span>
      <span className={tBtn} aria-hidden>🚫</span>
      <span className={tBtn} aria-hidden>🖨</span>
      <button onClick={() => onNavigate(today)} className={tBtn}>Today</button>
      <div className="ml-auto flex items-center gap-2">
        <span className="text-[11px] text-slate-500">Facility ▾</span>
        <span className={tBtn}>All selected ▾</span>
        <button onClick={() => onNavigate(addDays(date, 1))} className={tBtn} aria-label="Next day">›</button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------- side panel
function SidePanel({
  date,
  today,
  providers,
  visible,
  onToggle,
  onPickDay,
}: {
  date: string;
  today: string;
  providers: ScheduleProvider[];
  visible: Set<string>;
  onToggle: (id: string) => void;
  onPickDay: (iso: string) => void;
}) {
  return (
    <aside className="flex w-56 flex-shrink-0 flex-col overflow-y-auto border-r border-slate-300 bg-slate-100">
      <MiniCalendar date={date} today={today} onPickDay={onPickDay} />

      <div className="border-t border-slate-300 px-2 py-2">
        <div className="mb-1 flex items-center gap-1 text-[11px] font-semibold text-slate-600">
          <span aria-hidden>👥</span> My Providers
        </div>
        <input
          placeholder="Search…"
          className="mb-2 w-full rounded border border-slate-300 px-2 py-1 text-[11px] focus:outline-none"
        />
        <label className="flex items-center gap-2 border-b border-slate-200 py-1 text-[11px] text-slate-500">
          <input
            type="checkbox"
            checked={providers.every((p) => visible.has(p.id))}
            onChange={() =>
              providers.forEach((p) => {
                const all = providers.every((q) => visible.has(q.id));
                if (all === visible.has(p.id)) onToggle(p.id);
              })
            }
          />
          All
        </label>
        {providers.map((p) => (
          <label
            key={p.id}
            className="flex items-center gap-2 border-b border-slate-200 py-1 text-[11px] text-slate-700"
          >
            <input
              type="checkbox"
              checked={visible.has(p.id)}
              onChange={() => onToggle(p.id)}
            />
            {p.name}
          </label>
        ))}
        {["EKG", "CCM Manager", "Lab Only", "LAZER"].map((r) => (
          <label
            key={r}
            className="flex items-center gap-2 border-b border-slate-200 py-1 text-[11px] text-slate-400"
          >
            <input type="checkbox" disabled />
            {r}
          </label>
        ))}
      </div>
    </aside>
  );
}

function MiniCalendar({
  date,
  today,
  onPickDay,
}: {
  date: string;
  today: string;
  onPickDay: (iso: string) => void;
}) {
  const sel = isoToUtc(date);
  const [view, setView] = useState({
    y: sel.getUTCFullYear(),
    m: sel.getUTCMonth(),
  });

  const cells = useMemo(() => {
    const first = new Date(Date.UTC(view.y, view.m, 1));
    const startDow = first.getUTCDay();
    const daysInMonth = new Date(Date.UTC(view.y, view.m + 1, 0)).getUTCDate();
    const out: (string | null)[] = [];
    for (let i = 0; i < startDow; i++) out.push(null);
    for (let d = 1; d <= daysInMonth; d++) {
      out.push(utcToIso(new Date(Date.UTC(view.y, view.m, d))));
    }
    return out;
  }, [view]);

  const shift = (n: number) => {
    const d = new Date(Date.UTC(view.y, view.m + n, 1));
    setView({ y: d.getUTCFullYear(), m: d.getUTCMonth() });
  };

  return (
    <div className="px-2 py-2">
      <div className="mb-1 flex items-center justify-between text-[11px] font-semibold text-slate-600">
        <button onClick={() => shift(-1)} className="px-1 hover:text-slate-900" aria-label="Previous month">‹</button>
        <span>{MONTHS[view.m]} {view.y}</span>
        <button onClick={() => shift(1)} className="px-1 hover:text-slate-900" aria-label="Next month">›</button>
      </div>
      <div className="grid grid-cols-7 text-center text-[9px] text-slate-400">
        {DOW.map((d) => <span key={d} className="py-0.5">{d}</span>)}
      </div>
      <div className="grid grid-cols-7 text-center text-[10px]">
        {cells.map((iso, i) =>
          iso === null ? (
            <span key={`e${i}`} />
          ) : (
            <button
              key={iso}
              onClick={() => onPickDay(iso)}
              className={`m-px rounded py-0.5 ${
                iso === date
                  ? "bg-sky-600 font-bold text-white"
                  : iso === today
                    ? "bg-amber-200 font-semibold text-amber-800"
                    : "text-slate-600 hover:bg-slate-200"
              }`}
            >
              {isoToUtc(iso).getUTCDate()}
            </button>
          ),
        )}
      </div>
      <button
        onClick={() => onPickDay(today)}
        className="mt-1 w-full rounded border border-amber-300 bg-amber-50 py-0.5 text-[10px] font-semibold text-amber-700 hover:bg-amber-100"
      >
        Today
      </button>
    </div>
  );
}

// ---------------------------------------------------------------- grid
function Grid({
  date,
  columns,
  appointments,
}: {
  date: string;
  columns: ScheduleProvider[];
  appointments: ScheduleAppointment[];
}) {
  // strong hourly line + faint 15-min line, drawn as a background gradient
  const gridLines = {
    backgroundImage: `repeating-linear-gradient(to bottom, transparent 0, transparent ${ROW_H - 1}px, #e5e7eb ${ROW_H - 1}px, #e5e7eb ${ROW_H}px), repeating-linear-gradient(to bottom, transparent 0, transparent ${ROW_H * SLOTS_PER_HOUR - 1}px, #cbd5e1 ${ROW_H * SLOTS_PER_HOUR - 1}px, #cbd5e1 ${ROW_H * SLOTS_PER_HOUR}px)`,
  } as const;

  return (
    <div className="flex min-w-0 flex-1 flex-col bg-white">
      <div className="flex-shrink-0 border-b border-slate-300 bg-slate-50 py-1 text-center text-xs font-semibold text-slate-600">
        {longDate(date)}
      </div>

      <div className="min-h-0 flex-1 overflow-auto">
        {/* provider header (sticky) */}
        <div className="sticky top-0 z-10 flex border-b border-slate-300 bg-gradient-to-b from-slate-100 to-slate-200">
          <div className="w-14 flex-shrink-0 border-r border-slate-300" />
          {columns.length === 0 ? (
            <div className="flex-1 py-2 text-center text-[11px] text-slate-400">
              No providers selected
            </div>
          ) : (
            columns.map((p) => (
              <div
                key={p.id}
                className="min-w-[150px] flex-1 border-r border-slate-300 py-1.5 text-center text-xs font-semibold text-slate-700"
              >
                {p.name}
                <div className="text-[10px] font-normal text-slate-500">{p.specialty}</div>
              </div>
            ))
          )}
        </div>

        {/* body: time gutter + provider columns */}
        <div className="flex" style={{ height: BODY_H }}>
          <div className="w-14 flex-shrink-0 border-r border-slate-300 bg-slate-50">
            {Array.from({ length: ROWS }).map((_, i) => {
              const min = START_MIN + i * SLOT;
              return (
                <div
                  key={i}
                  className={`pr-1 text-right text-[9px] text-slate-400 ${
                    min % 60 === 0 ? "font-semibold text-slate-500" : ""
                  }`}
                  style={{ height: ROW_H, lineHeight: `${ROW_H}px` }}
                >
                  {timeLabel(min)}
                </div>
              );
            })}
          </div>

          {columns.map((p) => {
            const appts = appointments.filter((a) => a.providerId === p.id);
            const hasWindow = p.availStartMin != null && p.availEndMin != null;
            return (
              <div
                key={p.id}
                className="relative min-w-[150px] flex-1 border-r border-slate-300 bg-slate-100"
                style={{ height: BODY_H }}
              >
                {/* available working window (blue) vs off-hours (gray base) */}
                {hasWindow && (
                  <div
                    className="absolute inset-x-0 bg-sky-50"
                    style={{
                      top: clampTop(p.availStartMin!),
                      height: clampHeight(p.availStartMin!, p.availEndMin!),
                    }}
                  />
                )}
                {/* grid lines overlay */}
                <div className="pointer-events-none absolute inset-0" style={gridLines} />

                {appts.map((a) => (
                  <AppointmentBlock key={a.id} appt={a} />
                ))}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function clampTop(startMin: number): number {
  const clamped = Math.max(startMin, START_MIN);
  return ((clamped - START_MIN) / SLOT) * ROW_H;
}
function clampHeight(startMin: number, endMin: number): number {
  const top = Math.max(startMin, START_MIN);
  const bottom = Math.min(endMin, END_MIN);
  return Math.max(((bottom - top) / SLOT) * ROW_H, 0);
}

function AppointmentBlock({ appt }: { appt: ScheduleAppointment }) {
  const top = clampTop(appt.startMinutes);
  const height = Math.max(clampHeight(appt.startMinutes, appt.endMinutes), ROW_H);
  return (
    <div
      className="absolute inset-x-0.5 overflow-hidden rounded-sm border border-sky-400 bg-sky-100 px-1 py-0.5 text-[9px] leading-tight text-slate-700 shadow-sm"
      style={{ top, height }}
      title={`${appt.patientName} · ${appt.visitType} · ${appt.status}`}
    >
      <span className="mr-1 inline-block h-2 w-2 rounded-sm bg-emerald-500 align-middle" />
      <span className="font-semibold">{appt.patientName}</span>{" "}
      <span className="text-slate-500">{appt.patientDob}</span>{" "}
      <span className="text-slate-500">{appt.patientPhone}</span>
    </div>
  );
}
