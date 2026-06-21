"""CHW dashboard endpoints — the single surface the dashboard talks to.

  GET   /api/tasks                 → enriched task list (joins patients/voicemails)
  PATCH /api/tasks/{id}/decision   → the one decision executor (approve/reject/...)
  POST  /api/demo/baseline         → snapshot current demo state
  POST  /api/demo/reset            → restore to the saved baseline
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from . import demo, service
from .repo import TasksRepo

router = APIRouter()


@router.get("/api/tasks")
def get_tasks() -> list[dict]:
    return service.list_tasks(TasksRepo())


class DecisionBody(BaseModel):
    decision: str
    note: str | None = None
    status: str | None = None  # only used by `reopen`
    chw: str | None = None


@router.patch("/api/tasks/{task_id}/decision")
def decide(task_id: str, body: DecisionBody) -> dict:
    if body.decision not in service.DECISIONS:
        raise HTTPException(status_code=400, detail=f"invalid decision: {body.decision}")
    task, notice = service.apply_decision(
        TasksRepo(), task_id, body.decision, note=body.note, status=body.status, chw=body.chw
    )
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    return {"task": task, "notice": notice}


@router.post("/api/demo/baseline")
def save_baseline() -> dict:
    return demo.save_baseline(TasksRepo())


@router.post("/api/demo/reset")
def reset_demo() -> dict:
    return demo.reset(TasksRepo())
