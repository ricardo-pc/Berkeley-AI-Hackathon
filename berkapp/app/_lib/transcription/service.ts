import "server-only";

import { requestDeepgramTranscription } from "./deepgram";
import type { DeepgramResponse, TranscriptionResponse, Utterance } from "./types";

export async function transcribeAudio(
  audioBytes: ArrayBuffer,
  filename?: string,
  contentType?: string,
): Promise<TranscriptionResponse> {
  const rawResponse = await requestDeepgramTranscription(audioBytes, filename, contentType);
  return normalizeDeepgramResponse(rawResponse);
}

export function normalizeDeepgramResponse(rawResponse: DeepgramResponse): TranscriptionResponse {
  const metadata = rawResponse.metadata ?? {};
  const results = rawResponse.results ?? {};
  const alternative = firstAlternative(results);
  const providerRequestId =
    metadata.request_id === undefined || metadata.request_id === null ? null : String(metadata.request_id);

  return {
    id: providerRequestId ? `tr_${providerRequestId}` : `tr_${crypto.randomUUID().replaceAll("-", "")}`,
    transcript: String(alternative?.transcript ?? ""),
    confidence: asNumber(alternative?.confidence),
    duration: asNumber(metadata.duration),
    utterances: (results.utterances ?? []).map(normalizeUtterance),
    provider: "deepgram",
    provider_request_id: providerRequestId,
    raw_provider_response: rawResponse,
  };
}

function firstAlternative(results: NonNullable<DeepgramResponse["results"]>) {
  return results.channels?.[0]?.alternatives?.[0] ?? {};
}

function normalizeUtterance(utterance: Record<string, unknown>): Utterance {
  return {
    id: utterance.id === undefined || utterance.id === null ? null : String(utterance.id),
    start: asNumber(utterance.start),
    end: asNumber(utterance.end),
    confidence: asNumber(utterance.confidence),
    channel: asInteger(utterance.channel),
    speaker: asInteger(utterance.speaker),
    transcript: String(utterance.transcript ?? ""),
    words: Array.isArray(utterance.words) ? (utterance.words as Record<string, unknown>[]) : [],
  };
}

function asNumber(value: unknown) {
  if (value === undefined || value === null) {
    return null;
  }

  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function asInteger(value: unknown) {
  const parsed = asNumber(value);
  return parsed === null ? null : Math.trunc(parsed);
}

