from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import httpx
from fastapi.responses import JSONResponse

from .schemas import IntakeExtraction, IntakeRequestDetails, to_plain_dict


API_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = API_ROOT.parent.parent
ORCHESTRATOR_ROOT = API_ROOT.parent / "orchestrator"

sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(ORCHESTRATOR_ROOT))

from backend.orchestrator.main import app as orchestrator_app  # noqa: E402


ORCHESTRATOR_BASE_URL = os.getenv("ORCHESTRATOR_BASE_URL")


async def route_intake_to_orchestrator(
    intake: IntakeExtraction,
    *,
    task_id: str | None = None,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for request in _workflow_requests(intake):
        routed_intake = _intake_with_request(intake, request)
        path_or_response = _orchestrator_path_for(request.type)
        if isinstance(path_or_response, JSONResponse):
            results.append(await _json_response_payload(path_or_response, request.type))
            continue

        response = await _post_to_orchestrator(
            path_or_response,
            {"intake": routed_intake, "task_id": task_id},
        )
        results.append(
            {
                "request_type": request.type,
                "orchestrator_path": path_or_response,
                "status_code": response.status_code,
                "result": _response_json(response),
            }
        )
    return results


async def route_workflow_payload_to_orchestrator(
    intake: IntakeExtraction,
    *,
    path: str | None = None,
    task_id: str | None = None,
) -> JSONResponse:
    resolved_path = path or _orchestrator_path_for(intake.request.type)
    if isinstance(resolved_path, JSONResponse):
        return resolved_path

    response = await _post_to_orchestrator(
        resolved_path,
        {"intake": _sanitize_intake_dict(intake), "task_id": task_id},
    )
    return JSONResponse(status_code=response.status_code, content=_response_json(response))


def _workflow_requests(intake: IntakeExtraction) -> list[IntakeRequestDetails]:
    if intake.requests:
        return intake.requests
    return [intake.request]


def _intake_with_request(intake: IntakeExtraction, request: IntakeRequestDetails) -> dict[str, Any]:
    payload = _sanitize_intake_dict(intake)
    request_payload = to_plain_dict(request)
    payload["request"] = request_payload
    payload["requests"] = [request_payload]
    return payload


def _sanitize_intake_dict(intake: IntakeExtraction) -> dict[str, Any]:
    return to_plain_dict(intake)


def _orchestrator_path_for(request_type: str | None) -> str | JSONResponse:
    aliases = {
        "refill": "/api/refill",
        "prescription_refill": "/api/refill",
        "reschedule": "/api/reschedule",
        "message_relay": "/api/message-relay",
    }
    normalized = (request_type or "").strip().lower()
    path = aliases.get(normalized)
    if path:
        return path
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "unsupported_request_type",
                "message": f"No orchestrator route exists for intake.request.type={request_type!r}.",
            }
        },
    )


async def _post_to_orchestrator(path: str, payload: dict[str, Any]) -> httpx.Response:
    if ORCHESTRATOR_BASE_URL:
        async with httpx.AsyncClient(base_url=ORCHESTRATOR_BASE_URL, timeout=90.0) as client:
            return await client.post(path, json=payload)

    transport = httpx.ASGITransport(app=orchestrator_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://orchestrator") as client:
        return await client.post(path, json=payload)


def _response_json(response: httpx.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError:
        return {"error": {"code": "invalid_orchestrator_response", "message": response.text}}
    return payload if isinstance(payload, dict) else {"result": payload}


async def _json_response_payload(response: JSONResponse, request_type: str | None) -> dict[str, Any]:
    return {
        "request_type": request_type,
        "orchestrator_path": None,
        "status_code": response.status_code,
        "result": _decode_json_response(response),
    }


def _decode_json_response(response: JSONResponse) -> dict[str, Any]:
    import json

    payload = json.loads(response.body.decode("utf-8"))
    return payload if isinstance(payload, dict) else {"result": payload}
