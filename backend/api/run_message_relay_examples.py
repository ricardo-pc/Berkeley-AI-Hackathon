"""Run a batch of example messages through the message relay agent.

Reads demo/message_relay_examples/inputs.json, runs each message through the
live agent (read-only — no task_id, so nothing is written to the DB), prints a
summary table, and saves the full input+output pairs to outputs.json.

Usage:
    cd backend/api && source .venv/bin/activate
    python run_message_relay_examples.py
"""

from __future__ import annotations

import json
import pathlib
import sys

ORCHESTRATOR_ROOT = pathlib.Path(__file__).resolve().parents[1] / "orchestrator"
sys.path.insert(0, str(ORCHESTRATOR_ROOT))

from message_relay.repo import SupabaseMessageRelayRepo
from message_relay.service import run_message_relay_check

EXAMPLES_DIR = pathlib.Path(__file__).resolve().parents[2] / "demo" / "message_relay_examples"
INPUTS_PATH = EXAMPLES_DIR / "inputs.json"
OUTPUTS_PATH = EXAMPLES_DIR / "outputs.json"


def main() -> None:
    inputs = json.loads(INPUTS_PATH.read_text())
    repo = SupabaseMessageRelayRepo()

    results = []
    print(f"Running {len(inputs)} examples through the message relay agent...\n")
    header = f"{'id':<26} {'route':<10} {'status':<16} {'category':<28} flags"
    print(header)
    print("-" * len(header))

    for ex in inputs:
        output = run_message_relay_check(
            patient_id=ex["patient_id"],
            first_name=ex["first_name"],
            last_name=ex["last_name"],
            dob=ex["dob"],
            message=ex["message"],
            repo=repo,  # no task_id -> read-only
        )
        mr = output["agent_checks"]["message_relay"]
        flag = "⚑ " + output["flagged_reason"] if output["flagged_reason"] else ""
        print(
            f"{ex['id']:<26} {output['route']:<10} {output['status']:<16} "
            f"{str(mr.get('category')):<28} {flag}"
        )
        results.append({"input": ex, "output": output})

    OUTPUTS_PATH.write_text(json.dumps(results, indent=2) + "\n")
    print(f"\nSaved {len(results)} input/output pairs to {OUTPUTS_PATH}")


if __name__ == "__main__":
    main()
