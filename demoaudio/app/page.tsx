import AudioTranscriber from "./AudioTranscriber";

// Header chrome mirrors the /dashboard AppHeader: teal gradient, white text,
// a sky-600 logo chip, and a status pill on the right.
export default function Home() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-teal-900 bg-gradient-to-b from-teal-700 to-teal-900 text-white">
        <div className="mx-auto flex w-full max-w-4xl items-center gap-3 px-6 py-4">
          <span
            className="grid size-9 flex-none place-items-center rounded-[6px] bg-sky-600"
            aria-hidden="true"
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M2 10v3" />
              <path d="M6 6v11" />
              <path d="M10 3v18" />
              <path d="M14 8v7" />
              <path d="M18 5v13" />
              <path d="M22 10v3" />
            </svg>
          </span>
          <div className="leading-tight">
            <p className="text-base font-extrabold tracking-wide">Otomedi</p>
          </div>
          <div className="ml-auto flex items-center gap-2 rounded-full bg-white/10 px-3 py-1.5 font-mono text-[11px] text-white/80">
            <span
              className="size-1.5 rounded-full bg-emerald-400"
              aria-hidden="true"
            />
            API CONNECTED
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-4xl flex-1 px-6 pb-20">
        <AudioTranscriber />
      </main>
    </div>
  );
}
