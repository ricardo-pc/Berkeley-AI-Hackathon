from __future__ import annotations

import argparse
import json
import sys

from .errors import PrescriptionFulfillmentError, error_payload
from .repo import SupabasePrescriptionFulfillmentRepo
from .service import fill_prescription


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write a pre-approved prescription refill into Supabase.")
    parser.add_argument("--patient-id", required=True)
    parser.add_argument("--first-name", required=True)
    parser.add_argument("--last-name", required=True)
    parser.add_argument("--dob", required=True, help="ISO date, e.g. 1978-03-12")
    parser.add_argument("--medication-name", required=True)
    parser.add_argument("--dosage", required=True)
    parser.add_argument("--instructions", required=True)
    parser.add_argument("--provider-id", required=True)
    parser.add_argument("--pretty", action="store_true")
    return parser


def run(args: argparse.Namespace) -> dict:
    repo = SupabasePrescriptionFulfillmentRepo()
    return fill_prescription(
        patient_id=args.patient_id,
        first_name=args.first_name,
        last_name=args.last_name,
        dob=args.dob,
        medication_name=args.medication_name,
        dosage=args.dosage,
        instructions=args.instructions,
        provider_id=args.provider_id,
        repo=repo,
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        payload = run(args)
    except PrescriptionFulfillmentError as exc:
        print(json.dumps(error_payload(exc)), file=sys.stderr)
        return 1

    print(json.dumps(payload, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
