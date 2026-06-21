from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

from .errors import SchedulerError, error_payload
from .repo import SupabaseSchedulerRepo
from .service import book_appointment


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Book a pre-approved appointment slot into Supabase.")
    parser.add_argument("--patient-id", required=True)
    parser.add_argument("--first-name", required=True)
    parser.add_argument("--last-name", required=True)
    parser.add_argument("--dob", required=True, help="ISO date, e.g. 1978-03-12")
    parser.add_argument("--provider-id", required=True)
    parser.add_argument("--start", required=True, help="Slot start, ISO 8601.")
    parser.add_argument("--end", required=True, help="Slot end, ISO 8601.")
    parser.add_argument("--cancel-appointment-id", help="Existing appointment to mark rescheduled.")
    parser.add_argument("--visit-type", default="follow_up")
    parser.add_argument("--pretty", action="store_true")
    return parser


def run(args: argparse.Namespace) -> dict:
    repo = SupabaseSchedulerRepo()
    return book_appointment(
        patient_id=args.patient_id,
        first_name=args.first_name,
        last_name=args.last_name,
        dob=args.dob,
        provider_id=args.provider_id,
        start_time=datetime.fromisoformat(args.start),
        end_time=datetime.fromisoformat(args.end),
        cancel_appointment_id=args.cancel_appointment_id,
        visit_type=args.visit_type,
        repo=repo,
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        payload = run(args)
    except SchedulerError as exc:
        print(json.dumps(error_payload(exc)), file=sys.stderr)
        return 1

    print(json.dumps(payload, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
