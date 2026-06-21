from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .errors import ConfirmationError, error_payload
from .service import send_confirmation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Send a confirmation text for a successfully executed refill or reschedule."
    )
    parser.add_argument("--task-type", required=True, choices=["prescription_refill", "reschedule", "message_relay"])
    parser.add_argument("--phone-number", required=True)
    parser.add_argument(
        "--result-json",
        required=True,
        help="Path to a JSON file containing the executor's output (scheduler/prescription_fulfillment).",
    )
    parser.add_argument("--pretty", action="store_true")
    return parser


def run(args: argparse.Namespace) -> dict | None:
    result = json.loads(Path(args.result_json).read_text(encoding="utf-8"))
    return send_confirmation(
        task_type=args.task_type,
        phone_number=args.phone_number,
        result=result,
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        payload = run(args)
    except ConfirmationError as exc:
        print(json.dumps(error_payload(exc)), file=sys.stderr)
        return 1

    print(json.dumps(payload, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
