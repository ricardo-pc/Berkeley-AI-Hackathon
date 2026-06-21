// Same-origin proxy to the voicemail STT API. The upstream Heroku service does
// not send CORS headers (an OPTIONS preflight 405s), so the browser can't call
// it directly — we forward the uploaded file server-side instead.
//
// Override the upstream with STT_API_URL in .env.local if needed.

const STT_API_URL =
  process.env.STT_API_URL ??
  "https://voice-to-text-b3d4b8ef0ae3.herokuapp.com/api/voicemail/intake";

export const runtime = "nodejs";
// STT can be slow (cold dyno + Deepgram). Give it room where this matters.
export const maxDuration = 120;

export async function POST(request: Request) {
  let file: FormDataEntryValue | null;
  try {
    const form = await request.formData();
    file = form.get("file");
  } catch {
    return Response.json({ error: "Could not read the uploaded form data." }, { status: 400 });
  }

  if (!(file instanceof File)) {
    return Response.json({ error: "No audio file provided." }, { status: 400 });
  }

  const upstreamForm = new FormData();
  upstreamForm.append("file", file, file.name || "audio");

  let upstream: Response;
  try {
    upstream = await fetch(STT_API_URL, { method: "POST", body: upstreamForm });
  } catch (err) {
    return Response.json(
      { error: err instanceof Error ? `STT API unreachable: ${err.message}` : "STT API unreachable." },
      { status: 502 },
    );
  }

  const raw = await upstream.text();
  let data: { transcript?: string; intake?: unknown; error?: unknown } | null = null;
  try {
    data = JSON.parse(raw);
  } catch {
    data = null;
  }

  if (!upstream.ok) {
    const message =
      (data?.error as { message?: string })?.message ??
      (typeof data?.error === "string" ? data.error : null) ??
      `STT API error (${upstream.status}).`;
    return Response.json({ error: message }, { status: 502 });
  }

  return Response.json({
    transcript: data?.transcript ?? "",
    intake: data?.intake ?? null,
  });
}
