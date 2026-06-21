from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

from .claude_summary import generate_narrative
from .errors import SummaryError, error_payload
from .repo import SupabaseSummaryRepo
from .service import build_daily_digest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the front-desk daily digest from Supabase.")
    parser.add_argument("--since", help="Only include tasks created at/after this ISO 8601 timestamp.")
    parser.add_argument("--no-narrative", action="store_true", help="Skip the Claude-generated narrative paragraph.")
    parser.add_argument("--pretty", action="store_true")
    return parser


def run(args: argparse.Namespace) -> dict:
    repo = SupabaseSummaryRepo()
    since = datetime.fromisoformat(args.since) if args.since else None
    return build_daily_digest(
        since=since,
        repo=repo,
        summarize=None if args.no_narrative else generate_narrative,
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        payload = run(args)
    except SummaryError as exc:
        print(json.dumps(error_payload(exc)), file=sys.stderr)
        return 1

    print(json.dumps(payload, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
