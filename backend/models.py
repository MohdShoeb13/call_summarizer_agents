from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Segment(StrictModel):
    id: int = Field(ge=1)
    speaker: str = "Unknown"
    text: str = Field(min_length=1)


class Summary(StrictModel):
    issue: str
    key_points: list[str]
    resolution: Literal["resolved", "unresolved", "escalated", "unknown"]
    resolution_details: str
    action_items: list[str]
    tags: list[str]
    evidence_ids: list[int]


class Dimension(StrictModel):
    name: Literal["empathy", "professionalism", "tone", "resolution"]
    score: int | None = Field(ge=1, le=5)
    rationale: str
    evidence_ids: list[int]


class Quality(StrictModel):
    dimensions: list[Dimension] = Field(min_length=4, max_length=4)


class Event(StrictModel):
    stage: str
    message: str
    model: str | None = None


class CallResult(StrictModel):
    id: str
    title: str
    created_at: str
    status: Literal["queued", "processing", "completed", "failed", "interrupted"]
    stage: str
    demo: bool = False
    transcript: list[Segment] = Field(default_factory=list)
    summary: Summary | None = None
    quality: Quality | None = None
    overall_score: float | None = None
    events: list[Event] = Field(default_factory=list)
    error: str | None = None
    elapsed_seconds: float = 0


class SampleInfo(StrictModel):
    id: str
    title: str
    scenario: str


class Health(StrictModel):
    ready: bool
    provider: str = "OpenAI"
