from __future__ import annotations

import argparse
import json
import sys

from .errors import PrescriptionEligibilityError, error_payload
from .repo import SupabasePrescriptionEligibilityRepo
from .service import run_prescription_eligibility_check


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the prescription refill eligibility check against Supabase.")
    parser.add_argument("--patient-id", required=True)
    parser.add_argument("--medication-name", required=True)
    parser.add_argument("--dosage", required=True)
    parser.add_argument("--instructions", required=True)
    parser.add_argument("--task-id", help="tasks.id to write the result back to, if any.")
    parser.add_argument("--pretty", action="store_true")
    return parser


def run(args: argparse.Namespace) -> dict:
    repo = SupabasePrescriptionEligibilityRepo()
    return run_prescription_eligibility_check(
        patient_id=args.patient_id,
        medication_name=args.medication_name,
        dosage=args.dosage,
        instructions=args.instructions,
        task_id=args.task_id,
        repo=repo,
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        payload = run(args)
    except PrescriptionEligibilityError as exc:
        print(json.dumps(error_payload(exc)), file=sys.stderr)
        return 1

    print(json.dumps(payload, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
