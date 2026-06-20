"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

// eClinicalWorks-style login. Adds to the "before" story: even getting into the
// chart is a few steps. Any credentials work — this is a mockup.
export default function Login() {
  const router = useRouter();
  const [user, setUser] = useState("dalvarez");
  const [pw, setPw] = useState("••••••••");

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-teal-800 via-teal-700 to-slate-800 p-6">
      <div className="w-full max-w-sm">
        <div className="mb-6 text-center text-white">
          <div className="text-2xl font-bold tracking-tight">
            eClinical<span className="text-teal-300">Works</span>
            <sup className="ml-0.5 text-[10px]">®</sup>
          </div>
          <div className="text-xs text-teal-200">
            Berkeley Internal Medicine Associates
          </div>
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            router.push("/ehr");
          }}
          className="border border-slate-300 bg-white p-6 shadow-2xl"
        >
          <h1 className="mb-4 text-sm font-semibold text-slate-700">
            Provider / Staff Sign In
          </h1>
          <label className="mb-3 block">
            <span className="mb-0.5 block text-[11px] font-semibold uppercase tracking-wide text-slate-500">
              Username
            </span>
            <input
              value={user}
              onChange={(e) => setUser(e.target.value)}
              className="w-full rounded border border-slate-300 px-2 py-1.5 text-sm focus:border-sky-500 focus:outline-none"
            />
          </label>
          <label className="mb-4 block">
            <span className="mb-0.5 block text-[11px] font-semibold uppercase tracking-wide text-slate-500">
              Password
            </span>
            <input
              type="password"
              value={pw}
              onChange={(e) => setPw(e.target.value)}
              className="w-full rounded border border-slate-300 px-2 py-1.5 text-sm focus:border-sky-500 focus:outline-none"
            />
          </label>
          <button
            type="submit"
            className="w-full rounded border border-teal-800 bg-gradient-to-b from-teal-600 to-teal-700 py-2 text-sm font-semibold text-white hover:from-teal-700 hover:to-teal-800"
          >
            Sign In
          </button>
          <p className="mt-3 text-center text-[10px] text-slate-400">
            Demo mockup · any credentials proceed
          </p>
        </form>
      </div>
    </div>
  );
}
