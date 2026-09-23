from pydantic import BaseModel
from datetime import datetime
from typing import Any


class AlertOut(BaseModel):
    alert_id: str
    timestamp: datetime
    site_id: str | None
    zone_id: str | None
    machine_id: str | None
    operator_id: str | None
    task_id: str | None
    alert_type: str
    severity: str
    trigger_data: dict | None
    message: str
    recommended_action: str | None
    acknowledged: bool
    acknowledged_by: str | None
    acknowledged_at: datetime | None
    resolved: bool
    resolved_at: datetime | None

    model_config = {"from_attributes": True}


class AcknowledgeRequest(BaseModel):
    note: str | None = None


class IncidentOut(BaseModel):
    incident_id: str
    timestamp: datetime
    site_id: str | None
    zone_id: str | None
    machine_id: str | None
    operator_id: str | None
    category: str
    severity: str
    description: str
    status: str
    assigned_to: str | None
    resolution: str | None
    is_auto_created: bool

    model_config = {"from_attributes": True}


class IncidentCreate(BaseModel):
    machine_id: str | None = None
    operator_id: str | None = None
    task_id: str | None = None
    alert_id: str | None = None
    category: str
    severity: str
    description: str
    trigger_data: dict | None = None


class PrestartCheckItemIn(BaseModel):
    item_id: str
    passed: bool
    note: str | None = None


class PrestartSubmitRequest(BaseModel):
    machine_id: str
    operator_id: str
    items: list[PrestartCheckItemIn]


class PrestartResponse(BaseModel):
    check_id: str
    authorization_status: str  # AUTHORIZED|BLOCKED|REVIEW
    blocked_reasons: list[str]
    review_reasons: list[str]
    items: list[dict]
    performed_at: str
