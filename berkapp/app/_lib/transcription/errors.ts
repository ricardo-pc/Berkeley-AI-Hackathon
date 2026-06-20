export type TranscriptionErrorCode =
  | "transcription_error"
  | "missing_api_key"
  | "invalid_audio"
  | "provider_error";

export class TranscriptionError extends Error {
  code: TranscriptionErrorCode = "transcription_error";
  statusCode = 500;
}

export class MissingApiKeyError extends TranscriptionError {
  code: TranscriptionErrorCode = "missing_api_key";
  statusCode = 500;

  constructor() {
    super("Deepgram API key not configured.");
  }
}

export class InvalidAudioError extends TranscriptionError {
  code: TranscriptionErrorCode = "invalid_audio";
  statusCode = 400;

  constructor(message = "A non-empty audio file is required in form field 'file'.") {
    super(message);
  }
}

export class ProviderTranscriptionError extends TranscriptionError {
  code: TranscriptionErrorCode = "provider_error";
  statusCode = 502;
  providerStatusCode?: number;

  constructor(message = "Speech-to-text provider failed.", providerStatusCode?: number) {
    super(message);
    this.providerStatusCode = providerStatusCode;
  }
}

export function transcriptionErrorPayload(error: TranscriptionError) {
  return {
    error: {
      code: error.code,
      message: error.message,
    },
  };
}

