from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class Utterance(BaseModel):
    id: Optional[str] = None
    start: Optional[float] = None
    end: Optional[float] = None
    confidence: Optional[float] = None
    channel: Optional[int] = None
    speaker: Optional[int] = None
    transcript: str = ""
    words: List[Dict[str, Any]] = Field(default_factory=list)


class TranscriptionResponse(BaseModel):
    id: str
    transcript: str
    confidence: Optional[float] = None
    duration: Optional[float] = None
    utterances: List[Utterance] = Field(default_factory=list)
    provider: Literal["deepgram"] = "deepgram"
    provider_request_id: Optional[str] = None
    raw_provider_response: Dict[str, Any] = Field(default_factory=dict)


def to_plain_dict(model: BaseModel) -> dict:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()

