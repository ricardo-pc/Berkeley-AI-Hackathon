"""Snapshot-based demo reset (there's no seed script).

`save_baseline()` records the current demo state — each task's status/audit
fields plus the set of prescription/appointment/message row ids that exist
right now. `reset()` restores those task fields and deletes any
prescription/appointment/message rows created *after* the baseline (i.e. the
side effects of test approvals), so a test case can be re-run cleanly.

Save a baseline once when the demo is in the state you want to return to.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .repo import TasksRepo

BASELINE_PATH = Path(__file__).resolve().parent / "demo_baseline.json"
SIDE_EFFECT_TABLES = ("prescriptions", "appointments", "messages")
# Task fields the reset restores (everything a CHW decision can touch).
RESTORE_FIELDS = ("status", "approved_at", "approved_by", "rejected_at", "reviewed_at", "chw_note")


def save_baseline(repo: TasksRepo) -> dict[str, Any]:
    tasks = repo.list_tasks()
    snapshot = {
        "tasks": {t["id"]: {f: t.get(f) for f in RESTORE_FIELDS} for t in tasks},
        "side_effects": {table: repo.list_ids(table) for table in SIDE_EFFECT_TABLES},
    }
    BASELINE_PATH.write_text(json.dumps(snapshot, indent=2, default=str), encoding="utf-8")
    return {
        "saved": True,
        "tasks": len(snapshot["tasks"]),
        "side_effects": {k: len(v) for k, v in snapshot["side_effects"].items()},
    }


def reset(repo: TasksRepo) -> dict[str, Any]:
    if not BASELINE_PATH.exists():
        return {"reset": False, "error": "No baseline saved yet — POST /api/demo/baseline first."}

    snapshot = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))

    restored = 0
    for task_id, fields in snapshot.get("tasks", {}).items():
        repo.update_task(task_id, {f: fields.get(f) for f in RESTORE_FIELDS})
        restored += 1

    deleted: dict[str, int] = {}
    for table, baseline_ids in snapshot.get("side_effects", {}).items():
        current = set(repo.list_ids(table))
        extras = list(current - set(baseline_ids))
        repo.delete_ids(table, extras)
        deleted[table] = len(extras)

    return {"reset": True, "tasks_restored": restored, "rows_deleted": deleted}
