from pydantic import BaseModel
from datetime import datetime, date
from typing import Any


class OperatorSummary(BaseModel):
    operator_id: str
    employee_code: str
    name: str
    experience_years: int
    skill_level: int
    certification: str | None
    certification_expiry: date | None
    current_machine_id: str | None
    current_task_id: str | None
    shift_status: str
    safety_score: float
    authorization_status: str
    continuous_operating_minutes: float
    site_id: str | None

    model_config = {"from_attributes": True}


class OperatorDetail(OperatorSummary):
    email: str | None
    shift_start: datetime | None
    shift_end: datetime | None
    is_active: bool


class SafetyScoreComponent(BaseModel):
    score: float
    weight: float
    events_count: int | None = None
    incidents_count: int | None = None
    pending_modules: int | None = None


class SafetyScoreResponse(BaseModel):
    overall: float
    label: str = "Operational Safety Score (Demo Index)"
    components: dict[str, SafetyScoreComponent]
    computed_at: str


class TimelineEntry(BaseModel):
    entry_type: str  # TASK|BREAK|SAFETY_EVENT
    start_time: datetime
    end_time: datetime | None
    duration_minutes: float | None
    label: str
    machine_id: str | None
    zone_id: str | None
    status: str | None
    metadata: dict[str, Any] | None = None


class OperatorTimelineResponse(BaseModel):
    operator_id: str
    date: str
    entries: list[TimelineEntry]
    totals: dict[str, Any]
