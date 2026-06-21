"use client";

import { useCallback, useEffect, useRef, useState } from "react";

// ---------------------------------------------------------------------------
// Otomedi — audio upload + in-browser waveform + STT transcript.
// Decode/playback/seek logic is ported from the design handoff prototype
// (Audio Transcription.dc.html); the spectrogram was swapped for a peak
// waveform. The transcript is fetched from the real voicemail STT API via the
// same-origin /api/transcribe proxy.
// ---------------------------------------------------------------------------

type Stage = "idle" | "loading" | "ready" | "error";
type TranscriptStatus = "idle" | "loading" | "done" | "error";

// ---- pure helpers ---------------------------------------------------------

function fmt(s: number): string {
  if (!isFinite(s)) s = 0;
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${m}:${String(sec).padStart(2, "0")}`;
}

function fmtSize(b: number): string {
  if (b < 1024) return `${b} B`;
  if (b < 1048576) return `${(b / 1024).toFixed(0)} KB`;
  return `${(b / 1048576).toFixed(1)} MB`;
}

function toMono(buf: AudioBuffer): Float32Array {
  const n = buf.length;
  const out = new Float32Array(n);
  for (let ch = 0; ch < buf.numberOfChannels; ch++) {
    const d = buf.getChannelData(ch);
    for (let i = 0; i < n; i++) out[i] += d[i];
  }
  const inv = 1 / buf.numberOfChannels;
  for (let i = 0; i < n; i++) out[i] *= inv;
  return out;
}

// Draw a min/max peak waveform, bucketing the mono samples into one bar per
// device pixel column so it stays crisp at any width. Sky waveform on a light
// well to match the dashboard theme.
function paintWaveform(canvas: HTMLCanvasElement, mono: Float32Array | null): void {
  const dpr = window.devicePixelRatio || 1;
  const wCss = canvas.clientWidth || 800;
  const hCss = canvas.clientHeight || 160;
  const W = Math.round(wCss * dpr);
  const H = Math.round(hCss * dpr);
  canvas.width = W;
  canvas.height = H;
  const cx = canvas.getContext("2d");
  if (!cx) return;
  cx.clearRect(0, 0, W, H);

  const cy = H / 2;

  // Center (zero-amplitude) line.
  cx.strokeStyle = "rgba(148,163,184,0.45)"; // slate-400
  cx.lineWidth = Math.max(1, Math.floor(dpr));
  cx.beginPath();
  cx.moveTo(0, cy);
  cx.lineTo(W, cy);
  cx.stroke();

  if (!mono || mono.length === 0) return;

  const samplesPerCol = mono.length / W;
  const amp = cy * 0.92;
  cx.fillStyle = "#0284c7"; // sky-600
  const minBar = Math.max(1, Math.floor(dpr));
  for (let x = 0; x < W; x++) {
    const start = Math.floor(x * samplesPerCol);
    const end = Math.min(mono.length, Math.floor((x + 1) * samplesPerCol));
    let lo = 1.0;
    let hi = -1.0;
    for (let i = start; i < end; i++) {
      const v = mono[i];
      if (v < lo) lo = v;
      if (v > hi) hi = v;
    }
    if (end <= start) {
      lo = 0;
      hi = 0;
    }
    const y1 = cy - hi * amp;
    const y2 = cy - lo * amp;
    cx.fillRect(x, y1, minBar, Math.max(minBar, y2 - y1));
  }
}

// ---- component ------------------------------------------------------------

export default function AudioTranscriber() {
  const [stage, setStage] = useState<Stage>("idle");
  const [isDragOver, setIsDragOver] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [copied, setCopied] = useState(false);
  const [fileName, setFileName] = useState("");
  const [fileSizeStr, setFileSizeStr] = useState("");
  const [fileRateStr, setFileRateStr] = useState("");
  const [durationStr, setDurationStr] = useState("0:00");
  const [errorMsg, setErrorMsg] = useState("");
  const [transcript, setTranscript] = useState("");
  const [transcriptStatus, setTranscriptStatus] = useState<TranscriptStatus>("idle");
  const [transcriptError, setTranscriptError] = useState("");

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const playheadRef = useRef<HTMLDivElement>(null);
  const timeRef = useRef<HTMLDivElement>(null);
  const waveBoxRef = useRef<HTMLDivElement>(null);

  const durationRef = useRef(0);
  const monoRef = useRef<Float32Array | null>(null);
  const objectUrlRef = useRef<string | null>(null);
  const draggingRef = useRef(false);
  const ctxRef = useRef<AudioContext | null>(null);
  const copyTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const getAudioCtx = useCallback(() => {
    if (!ctxRef.current) {
      const AC =
        window.AudioContext ||
        (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      ctxRef.current = new AC();
    }
    return ctxRef.current;
  }, []);

  const redraw = useCallback(() => {
    if (canvasRef.current) paintWaveform(canvasRef.current, monoRef.current);
  }, []);

  const seekFromEvent = useCallback((e: PointerEvent | React.PointerEvent) => {
    const box = waveBoxRef.current;
    if (!box) return;
    const r = box.getBoundingClientRect();
    let x = (e.clientX - r.left) / r.width;
    x = Math.max(0, Math.min(1, x));
    const a = audioRef.current;
    if (a) a.currentTime = x * durationRef.current;
    if (playheadRef.current) playheadRef.current.style.left = `${x * 100}%`;
    if (timeRef.current) {
      timeRef.current.textContent = `${fmt(x * durationRef.current)} / ${fmt(durationRef.current)}`;
    }
  }, []);

  const togglePlay = useCallback(() => {
    const a = audioRef.current;
    if (!a) return;
    const ctx = getAudioCtx();
    if (ctx.state === "suspended") void ctx.resume();
    if (a.paused) {
      void a.play();
      setIsPlaying(true);
    } else {
      a.pause();
      setIsPlaying(false);
    }
  }, [getAudioCtx]);

  const onWavePointerDown = useCallback(
    (e: React.PointerEvent) => {
      draggingRef.current = true;
      seekFromEvent(e);
    },
    [seekFromEvent],
  );

  const startTranscription = useCallback(async (file: File) => {
    setTranscript("");
    setTranscriptError("");
    setTranscriptStatus("loading");
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch("/api/transcribe", { method: "POST", body: fd });
      const data = (await res.json().catch(() => ({}))) as { transcript?: string; error?: string };
      if (!res.ok) throw new Error(data.error || `Transcription failed (${res.status}).`);
      setTranscript(data.transcript ?? "");
      setTranscriptStatus("done");
    } catch (err) {
      setTranscriptError(err instanceof Error ? err.message : "Transcription failed.");
      setTranscriptStatus("error");
    }
  }, []);

  const processFile = useCallback(
    async (file: File) => {
      if (objectUrlRef.current) URL.revokeObjectURL(objectUrlRef.current);
      objectUrlRef.current = URL.createObjectURL(file);
      setFileName(file.name);
      setFileSizeStr(fmtSize(file.size));
      setStage("loading");

      // Transcription runs in parallel with the in-browser decode.
      void startTranscription(file);

      let audioBuf: AudioBuffer;
      try {
        const arr = await file.arrayBuffer();
        audioBuf = await getAudioCtx().decodeAudioData(arr.slice(0));
      } catch {
        setStage("error");
        setErrorMsg("This file isn't a supported or readable audio format.");
        return;
      }
      durationRef.current = audioBuf.duration;
      monoRef.current = toMono(audioBuf);
      setDurationStr(fmt(audioBuf.duration));
      setFileRateStr(`${(audioBuf.sampleRate / 1000).toFixed(1)} kHz`);
      setIsPlaying(false);
      setStage("ready");
    },
    [getAudioCtx, startTranscription],
  );

  const onFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const f = e.target.files?.[0];
      if (f) void processFile(f);
    },
    [processFile],
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);
      const f = e.dataTransfer.files?.[0];
      if (f) void processFile(f);
    },
    [processFile],
  );

  const reset = useCallback(() => {
    const a = audioRef.current;
    if (a) {
      a.pause();
      a.removeAttribute("src");
      a.load();
    }
    monoRef.current = null;
    if (fileInputRef.current) fileInputRef.current.value = "";
    setStage("idle");
    setIsPlaying(false);
    setIsDragOver(false);
    setTranscript("");
    setTranscriptStatus("idle");
    setTranscriptError("");
  }, []);

  const onCopy = useCallback(() => {
    void navigator.clipboard?.writeText(transcript);
    setCopied(true);
    if (copyTimerRef.current) clearTimeout(copyTimerRef.current);
    copyTimerRef.current = setTimeout(() => setCopied(false), 1500);
  }, [transcript]);

  // Window-level drag-to-seek + redraw on resize; cleanup on unmount.
  useEffect(() => {
    const onMove = (e: PointerEvent) => {
      if (draggingRef.current) seekFromEvent(e);
    };
    const onUp = () => {
      draggingRef.current = false;
    };
    const onResize = () => redraw();
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
    window.addEventListener("resize", onResize);
    return () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
      window.removeEventListener("resize", onResize);
      if (copyTimerRef.current) clearTimeout(copyTimerRef.current);
      if (objectUrlRef.current) URL.revokeObjectURL(objectUrlRef.current);
    };
  }, [seekFromEvent, redraw]);

  // When the Ready view mounts: wire the audio element and draw the waveform.
  useEffect(() => {
    if (stage !== "ready") return;
    const a = audioRef.current;
    if (a && objectUrlRef.current) {
      a.src = objectUrlRef.current;
      a.onended = () => setIsPlaying(false);
    }
    if (playheadRef.current) playheadRef.current.style.left = "0%";
    if (timeRef.current) timeRef.current.textContent = `${fmt(0)} / ${fmt(durationRef.current)}`;
    redraw();
  }, [stage, redraw]);

  // Drive the playhead + timecode with rAF while playing (smooth), per the design.
  useEffect(() => {
    if (!isPlaying) return;
    let raf = 0;
    const frame = () => {
      const a = audioRef.current;
      if (!a) return;
      const dur = durationRef.current;
      const p = dur ? a.currentTime / dur : 0;
      if (playheadRef.current) playheadRef.current.style.left = `${p * 100}%`;
      if (timeRef.current) timeRef.current.textContent = `${fmt(a.currentTime)} / ${fmt(dur)}`;
      if (!a.paused && !a.ended) raf = requestAnimationFrame(frame);
    };
    raf = requestAnimationFrame(frame);
    return () => cancelAnimationFrame(raf);
  }, [isPlaying]);

  return (
    <>
      {stage === "idle" && (
        <div
          onClick={() => fileInputRef.current?.click()}
          onDrop={onDrop}
          onDragOver={(e) => {
            e.preventDefault();
            if (!isDragOver) setIsDragOver(true);
          }}
          onDragLeave={(e) => {
            e.preventDefault();
            setIsDragOver(false);
          }}
          className={`mt-16 cursor-pointer rounded-2xl border-[1.5px] border-dashed px-8 py-20 text-center transition-colors ${
            isDragOver ? "border-sky-600 bg-sky-50" : "border-slate-300 bg-white"
          }`}
        >
          <div className="mx-auto mb-6 grid size-16 place-items-center rounded-full bg-sky-50 text-sky-600">
            <svg
              width="26"
              height="26"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={1.8}
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M12 16V4" />
              <path d="m6 10 6-6 6 6" />
              <path d="M4 18v1a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-1" />
            </svg>
          </div>
          <h2 className="mb-2 text-2xl font-semibold tracking-tight text-slate-900">
            Drop an audio file to transcribe
          </h2>
          <p className="mb-7 text-sm text-slate-500">
            or click to browse — WAV · MP3 · M4A · FLAC · OGG
          </p>
          <span className="inline-flex items-center gap-2 rounded-lg bg-sky-600 px-5 py-2.5 text-sm font-semibold text-white">
            Choose file
          </span>
          <input
            ref={fileInputRef}
            type="file"
            accept="audio/*"
            onChange={onFileChange}
            className="hidden"
          />
        </div>
      )}

      {stage === "loading" && (
        <div className="mt-32 flex flex-col items-center gap-5">
          <div className="size-10 animate-spin rounded-full border-[3px] border-slate-200 border-t-sky-600" />
          <div className="text-center">
            <div className="text-base font-medium text-slate-900">Analyzing audio</div>
            <div className="mt-1 font-mono text-[13px] text-slate-500">
              decoding · drawing waveform
            </div>
          </div>
        </div>
      )}

      {stage === "error" && (
        <div className="mt-28 text-center">
          <div className="mb-2 text-lg font-semibold text-rose-600">Couldn&apos;t read that file</div>
          <div className="mb-6 text-sm text-slate-500">{errorMsg}</div>
          <button
            onClick={reset}
            className="rounded-lg border border-slate-300 bg-white px-5 py-2.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
          >
            Try another file
          </button>
        </div>
      )}

      {stage === "ready" && (
        <div className="mt-8 space-y-[18px]">
          {/* File meta bar */}
          <div className="flex items-center gap-4 rounded-xl border border-slate-200 bg-white px-[18px] py-[14px] shadow-sm">
            <div className="grid size-9 flex-none place-items-center rounded-lg bg-sky-50 text-sky-600">
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth={1.8}
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M9 18V5l12-2v13" />
                <circle cx="6" cy="18" r="3" />
                <circle cx="18" cy="16" r="3" />
              </svg>
            </div>
            <div className="min-w-0 flex-1">
              <div className="truncate text-sm font-medium text-slate-900">{fileName}</div>
              <div className="mt-0.5 font-mono text-[11.5px] text-slate-500">
                {fileSizeStr} · {fileRateStr} · {durationStr}
              </div>
            </div>
            <button
              onClick={reset}
              className="flex-none rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-[13px] font-medium text-slate-700 transition-colors hover:bg-slate-50"
            >
              Replace
            </button>
          </div>

          {/* Waveform panel */}
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="flex items-stretch gap-2.5">
              <div className="relative w-[46px] flex-none font-mono text-[10px] text-slate-400">
                <span className="absolute right-0 top-0">+1.0</span>
                <span className="absolute right-0 top-1/2 -translate-y-1/2">0</span>
                <span className="absolute bottom-0 right-0">−1.0</span>
              </div>
              <div
                ref={waveBoxRef}
                onPointerDown={onWavePointerDown}
                className="relative h-[160px] flex-1 cursor-pointer overflow-hidden rounded-md border border-slate-200 bg-slate-50"
                style={{ touchAction: "none" }}
              >
                <canvas ref={canvasRef} className="absolute inset-0 block size-full" />
                <div
                  ref={playheadRef}
                  className="pointer-events-none absolute bottom-0 top-0 w-0.5"
                  style={{ left: "0%", background: "#0369a1", boxShadow: "0 0 6px rgba(3,105,161,0.5)" }}
                />
              </div>
            </div>

            <div className="mt-3.5 flex items-center gap-[18px] pl-14">
              <button
                onClick={togglePlay}
                aria-label={isPlaying ? "Pause" : "Play"}
                className="grid size-[46px] flex-none place-items-center rounded-full bg-sky-600 text-white transition-colors hover:bg-sky-700"
              >
                {isPlaying ? (
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <rect x="5" y="4" width="5" height="16" rx="1" />
                    <rect x="14" y="4" width="5" height="16" rx="1" />
                  </svg>
                ) : (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M7 4v16l13-8z" />
                  </svg>
                )}
              </button>
              <div ref={timeRef} className="font-mono text-sm tracking-wide text-slate-600">
                0:00 / {durationStr}
              </div>
              <div className="ml-auto font-mono text-[11px] text-slate-400">click waveform to seek</div>
            </div>
          </div>

          {/* Transcript panel */}
          <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
            <div className="flex items-center gap-2.5 border-b border-slate-100 px-[18px] py-[14px]">
              <span className="text-sm font-semibold text-slate-900">Transcript</span>
              {transcriptStatus === "loading" && (
                <span className="rounded-md bg-amber-100 px-2 py-1 font-mono text-[10px] tracking-[0.1em] text-amber-700">
                  TRANSCRIBING…
                </span>
              )}
              {transcriptStatus === "done" && (
                <span className="rounded-md bg-sky-100 px-2 py-1 font-mono text-[10px] tracking-[0.1em] text-sky-700">
                  STT API
                </span>
              )}
              {transcriptStatus === "error" && (
                <span className="rounded-md bg-rose-100 px-2 py-1 font-mono text-[10px] tracking-[0.1em] text-rose-700">
                  FAILED
                </span>
              )}
              <button
                onClick={onCopy}
                disabled={transcriptStatus !== "done" || !transcript}
                className="ml-auto inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3.5 py-1.5 text-[13px] font-medium text-slate-700 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth={1.8}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <rect x="9" y="9" width="13" height="13" rx="2" />
                  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                </svg>
                {copied ? "Copied" : "Copy"}
              </button>
            </div>

            {transcriptStatus === "loading" && (
              <div className="flex items-center gap-3 px-[18px] py-12 text-slate-500">
                <div className="size-4 animate-spin rounded-full border-2 border-slate-200 border-t-sky-600" />
                <span className="font-mono text-[13px]">transcribing audio…</span>
              </div>
            )}

            {transcriptStatus === "error" && (
              <div className="px-[18px] py-10 text-sm text-rose-600">{transcriptError}</div>
            )}

            {transcriptStatus === "done" && (
              <textarea
                value={transcript}
                onChange={(e) => setTranscript(e.target.value)}
                spellCheck={false}
                placeholder="No speech detected in this recording."
                className="block min-h-[200px] w-full resize-y border-0 bg-transparent p-[18px] text-[15px] leading-relaxed text-slate-800 outline-none placeholder:text-slate-400"
              />
            )}

            <div className="border-t border-slate-100 px-[18px] py-[11px] font-mono text-[11px] text-slate-400">
              Transcribed from your uploaded audio via the voicemail STT API.
            </div>
          </div>
        </div>
      )}

      <audio ref={audioRef} className="hidden" />
    </>
  );
}
