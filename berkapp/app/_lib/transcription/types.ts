export type Utterance = {
  id: string | null;
  start: number | null;
  end: number | null;
  confidence: number | null;
  channel: number | null;
  speaker: number | null;
  transcript: string;
  words: Record<string, unknown>[];
};

export type TranscriptionResponse = {
  id: string;
  transcript: string;
  confidence: number | null;
  duration: number | null;
  utterances: Utterance[];
  provider: "deepgram";
  provider_request_id: string | null;
  raw_provider_response: Record<string, unknown>;
};

export type DeepgramResponse = {
  metadata?: {
    request_id?: unknown;
    duration?: unknown;
    [key: string]: unknown;
  };
  results?: {
    channels?: Array<{
      alternatives?: Array<{
        transcript?: unknown;
        confidence?: unknown;
        [key: string]: unknown;
      }>;
      [key: string]: unknown;
    }>;
    utterances?: Array<Record<string, unknown>>;
    [key: string]: unknown;
  };
  [key: string]: unknown;
};

