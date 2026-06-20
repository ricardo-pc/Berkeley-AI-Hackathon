from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

from .errors import ScheduleEligibilityError, error_payload
from .repo import SupabaseScheduleEligibilityRepo
from .service import run_schedule_eligibility_check


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the schedule adjustment eligibility check against Supabase.")
    parser.add_argument("--patient-id", required=True)
    parser.add_argument("--provider-id", required=True)
    parser.add_argument("--start", required=True, help="Requested start time, ISO 8601.")
    parser.add_argument("--end", required=True, help="Requested end time, ISO 8601.")
    parser.add_argument("--cancel-appointment-id", help="Existing appointment id being moved, if any.")
    parser.add_argument("--pretty", action="store_true")
    return parser


def run(args: argparse.Namespace) -> dict:
    repo = SupabaseScheduleEligibilityRepo()
    return run_schedule_eligibility_check(
        patient_id=args.patient_id,
        provider_id=args.provider_id,
        requested_start=datetime.fromisoformat(args.start),
        requested_end=datetime.fromisoformat(args.end),
        cancel_appointment_id=args.cancel_appointment_id,
        repo=repo,
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        payload = run(args)
    except ScheduleEligibilityError as exc:
        print(json.dumps(error_payload(exc)), file=sys.stderr)
        return 1

    print(json.dumps(payload, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
