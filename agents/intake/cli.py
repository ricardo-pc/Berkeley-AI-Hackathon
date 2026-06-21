from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .errors import IntakeAgentError, error_payload
from .schemas import to_plain_dict
from .service import run_intake_extraction


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract intake fields from Deepgram/STT JSON with Claude.")
    parser.add_argument("stt_json_file", help="Path to a Deepgram or normalized STT JSON file.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    parser.add_argument("--output", help="Optional path to save the extracted intake JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        stt_json = json.loads(Path(args.stt_json_file).read_text(encoding="utf-8"))
        result = to_plain_dict(run_intake_extraction(stt_json))
    except IntakeAgentError as exc:
        print(json.dumps(error_payload(exc)), file=sys.stderr)
        return 1
    except (OSError, json.JSONDecodeError) as exc:
        print(
            json.dumps(
                {
                    "error": {
                        "code": "invalid_stt_json_file",
                        "message": str(exc),
                    }
                }
            ),
            file=sys.stderr,
        )
        return 1

    indent = 2 if args.pretty else None
    output = json.dumps(result, indent=indent)

    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")

    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

