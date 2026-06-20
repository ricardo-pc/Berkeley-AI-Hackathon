import "server-only";

import {
  InvalidAudioError,
  MissingApiKeyError,
  ProviderTranscriptionError,
} from "./errors";
import type { DeepgramResponse } from "./types";

export const DEEPGRAM_LISTEN_URL = "https://api.deepgram.com/v1/listen";

export const DEEPGRAM_DEFAULT_PARAMS = {
  model: "nova-3",
  smart_format: "true",
  punctuate: "true",
  numerals: "true",
  utterances: "true",
} as const;

export function getDeepgramApiKey(apiKey = process.env.DEEPGRAM_API_KEY) {
  if (!apiKey) {
    throw new MissingApiKeyError();
  }

  return apiKey;
}

export function inferAudioContentType(filename?: string, contentType?: string) {
  if (contentType && contentType !== "application/octet-stream") {
    return contentType;
  }

  const extension = filename?.split(".").pop()?.toLowerCase();
  const overrides: Record<string, string> = {
    m4a: "audio/mp4",
    mp3: "audio/mpeg",
    ogg: "audio/ogg",
    opus: "audio/ogg",
    wav: "audio/wav",
    webm: "audio/webm",
  };

  return extension ? overrides[extension] ?? "application/octet-stream" : "application/octet-stream";
}

export async function requestDeepgramTranscription(
  audioBytes: ArrayBuffer,
  filename?: string,
  contentType?: string,
  apiKey?: string,
) {
  if (audioBytes.byteLength === 0) {
    throw new InvalidAudioError();
  }

  const searchParams = new URLSearchParams(DEEPGRAM_DEFAULT_PARAMS);
  const response = await fetch(`${DEEPGRAM_LISTEN_URL}?${searchParams.toString()}`, {
    method: "POST",
    headers: {
      Authorization: `Token ${getDeepgramApiKey(apiKey)}`,
      "Content-Type": inferAudioContentType(filename, contentType),
    },
    body: audioBytes,
  });

  if (!response.ok) {
    throw new ProviderTranscriptionError(await providerErrorMessage(response), response.status);
  }

  try {
    return (await response.json()) as DeepgramResponse;
  } catch {
    throw new ProviderTranscriptionError("Deepgram returned an invalid JSON response.");
  }
}

async function providerErrorMessage(response: Response) {
  try {
    const payload = (await response.json()) as Record<string, unknown>;
    const message = payload.err_msg ?? payload.message ?? payload.error;
    return message ? String(message) : "Deepgram speech-to-text request failed.";
  } catch {
    return "Deepgram speech-to-text request failed.";
  }
}
