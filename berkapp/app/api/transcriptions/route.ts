import { InvalidAudioError, TranscriptionError, transcriptionErrorPayload } from "@/app/_lib/transcription/errors";
import { transcribeAudio } from "@/app/_lib/transcription/service";

export const runtime = "nodejs";

export async function POST(request: Request) {
  try {
    const formData = await request.formData();
    const file = formData.get("file");

    if (!isUploadFile(file)) {
      return errorResponse(new InvalidAudioError());
    }

    const result = await transcribeAudio(await file.arrayBuffer(), file.name, file.type);
    return Response.json(result);
  } catch (error) {
    if (error instanceof TranscriptionError) {
      return errorResponse(error);
    }

    console.error("Unexpected transcription route error:", error);
    return Response.json(
      {
        error: {
          code: "transcription_error",
          message: "Transcription failed.",
        },
      },
      { status: 500 },
    );
  }
}

function isUploadFile(value: FormDataEntryValue | null): value is File {
  return typeof value === "object" && value !== null && "arrayBuffer" in value && "name" in value;
}

function errorResponse(error: TranscriptionError) {
  return Response.json(transcriptionErrorPayload(error), { status: error.statusCode });
}

