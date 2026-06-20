"use client";

// A demo-only overlay. It listens for every click inside the EHR and counts
// elapsed time, so during the pitch we can literally show "27 clicks / 4:12 to
// refill one prescription." Not part of a real EHR — it's our storytelling prop.

import { createContext, useContext, useEffect, useRef, useState } from "react";

type FrictionState = {
  clicks: number;
  seconds: number;
  screens: number;
  reset: () => void;
  noteScreen: () => void;
};

const FrictionContext = createContext<FrictionState | null>(null);

export function useFriction() {
  const ctx = useContext(FrictionContext);
  if (!ctx) throw new Error("useFriction must be used inside FrictionProvider");
  return ctx;
}

export function FrictionProvider({ children }: { children: React.ReactNode }) {
  const [clicks, setClicks] = useState(0);
  const [seconds, setSeconds] = useState(0);
  const [screens, setScreens] = useState(1);
  const [open, setOpen] = useState(true);
  const startedRef = useRef(false);

  useEffect(() => {
    const onClick = () => setClicks((c) => c + 1);
    window.addEventListener("click", onClick);
    return () => window.removeEventListener("click", onClick);
  }, []);

  useEffect(() => {
    const id = setInterval(() => {
      if (startedRef.current) setSeconds((s) => s + 1);
    }, 1000);
    return () => clearInterval(id);
  }, []);

  // start the timer on the first real click
  useEffect(() => {
    if (clicks > 0) startedRef.current = true;
  }, [clicks]);

  const reset = () => {
    setClicks(0);
    setSeconds(0);
    setScreens(1);
    startedRef.current = false;
  };
  const noteScreen = () => setScreens((s) => s + 1);

  const mm = String(Math.floor(seconds / 60)).padStart(2, "0");
  const ss = String(seconds % 60).padStart(2, "0");

  return (
    <FrictionContext.Provider value={{ clicks, seconds, screens, reset, noteScreen }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 select-none font-mono text-xs">
        {open ? (
          <div className="rounded-lg border border-amber-400 bg-amber-50 px-3 py-2 shadow-lg">
            <div className="mb-1 flex items-center justify-between gap-3">
              <span className="font-sans font-semibold text-amber-900">
                ⏱ Manual-effort meter
              </span>
              <button
                onClick={() => setOpen(false)}
                className="font-sans text-amber-700 hover:text-amber-900"
                aria-label="Hide meter"
              >
                ✕
              </button>
            </div>
            <div className="flex gap-4 text-amber-900">
              <span>
                <b className="text-base">{clicks}</b> clicks
              </span>
              <span>
                <b className="text-base">{screens}</b> screens
              </span>
              <span>
                <b className="text-base">
                  {mm}:{ss}
                </b>{" "}
                elapsed
              </span>
            </div>
            <button
              onClick={reset}
              className="mt-1 font-sans text-[11px] text-amber-700 underline hover:text-amber-900"
            >
              reset for demo
            </button>
          </div>
        ) : (
          <button
            onClick={() => setOpen(true)}
            className="rounded-full border border-amber-400 bg-amber-50 px-3 py-1 font-sans text-amber-900 shadow"
          >
            ⏱ {clicks} clicks
          </button>
        )}
      </div>
    </FrictionContext.Provider>
  );
}
