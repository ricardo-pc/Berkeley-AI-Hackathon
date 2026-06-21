from __future__ import annotations

import argparse
import json
import sys

from .errors import MessageRelayError, error_payload
from .repo import SupabaseMessageRelayRepo
from .service import run_message_relay_check


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the message relay eligibility check against Supabase.")
    parser.add_argument("--patient-id", required=True)
    parser.add_argument("--first-name", required=True)
    parser.add_argument("--last-name", required=True)
    parser.add_argument("--dob", required=True, help="ISO date, e.g. 1988-09-18")
    parser.add_argument("--message", required=True, help="The patient's message text.")
    parser.add_argument("--task-id", help="Existing task row to update, if any.")
    parser.add_argument("--pretty", action="store_true")
    return parser


def run(args: argparse.Namespace) -> dict:
    repo = SupabaseMessageRelayRepo()
    return run_message_relay_check(
        patient_id=args.patient_id,
        first_name=args.first_name,
        last_name=args.last_name,
        dob=args.dob,
        message=args.message,
        task_id=args.task_id,
        repo=repo,
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        payload = run(args)
    except MessageRelayError as exc:
        print(json.dumps(error_payload(exc)), file=sys.stderr)
        return 1

    print(json.dumps(payload, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
