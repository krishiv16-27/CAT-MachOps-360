from pydantic import BaseModel
from datetime import datetime
from typing import Any


class TaskOut(BaseModel):
    task_id: str
    site_id: str
    zone_id: str | None
    machine_id: str | None
    operator_id: str | None
    task_type: str
    description: str | None
    material_type: str | None
    target_quantity: float | None
    completed_quantity: float
    unit: str | None
    status: str
    scheduled_start: datetime | None
    actual_start: datetime | None
    actual_end: datetime | None
    estimated_duration_minutes: float | None
    actual_duration_minutes: float | None
    predicted_duration_minutes: float | None
    weather_condition: str | None
    terrain_type: str | None
    delay_reason: str | None
    priority: int

    model_config = {"from_attributes": True}


class TaskCreate(BaseModel):
    site_id: str
    zone_id: str | None = None
    machine_id: str | None = None
    operator_id: str | None = None
    task_type: str
    description: str | None = None
    material_type: str | None = None
    target_quantity: float | None = None
    unit: str | None = None
    scheduled_start: datetime | None = None
    estimated_duration_minutes: float | None = None
    priority: int = 2


class TaskUpdate(BaseModel):
    status: str | None = None
    completed_quantity: float | None = None
    delay_reason: str | None = None
    actual_end: datetime | None = None


class ETAPredictionRequest(BaseModel):
    task_type: str
    machine_type: str
    machine_age_years: float = 2.0
    operator_skill_level: int = 3
    operator_experience_years: float = 3.0
    target_quantity: float = 100.0
    material_type: str = "CLAY"
    weather_condition: str = "CLEAR"
    temperature_celsius: float = 22.0
    rainfall_mm: float = 0.0
    wind_speed_kmh: float = 10.0
    terrain_type: str = "FLAT"
    machine_load_percent: float = 70.0
    historical_avg_duration_minutes: float | None = None


class ETAPredictionResponse(BaseModel):
    predicted_minutes: float
    confidence_interval: list[float]
    mock: bool = False
    message: str | None = None
    features_used: dict[str, Any] | None = None
