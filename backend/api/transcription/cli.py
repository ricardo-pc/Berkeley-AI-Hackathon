from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from .deepgram_client import infer_audio_content_type
from .errors import InvalidAudioError, TranscriptionError, error_payload
from .schemas import to_plain_dict
from .service import transcribe_audio


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Transcribe an audio file with Deepgram.")
    parser.add_argument("audio_file", help="Path to a local audio file.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    parser.add_argument("--output", help="Optional path to save the JSON response.")
    return parser


async def run(args: argparse.Namespace) -> dict:
    audio_path = Path(args.audio_file)
    if not audio_path.is_file():
        raise InvalidAudioError(f"Audio file not found: {audio_path}")

    audio_bytes = audio_path.read_bytes()
    result = await transcribe_audio(
        audio_bytes,
        filename=audio_path.name,
        content_type=infer_audio_content_type(audio_path.name),
    )
    return to_plain_dict(result)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        payload = asyncio.run(run(args))
    except TranscriptionError as exc:
        print(json.dumps(error_payload(exc)), file=sys.stderr)
        return 1

    indent = 2 if args.pretty else None
    output = json.dumps(payload, indent=indent)

    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")

    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

