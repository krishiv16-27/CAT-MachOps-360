from pydantic import BaseModel
from datetime import datetime
from typing import Any


class MachineSummary(BaseModel):
    machine_id: str
    machine_code: str
    machine_type: str
    model_name: str
    site_id: str | None
    zone_id: str | None
    status: str
    current_operator_id: str | None
    current_task_id: str | None
    engine_hours: float
    last_fuel_level_pct: float | None
    last_engine_temp_c: float | None
    last_health_score: float | None
    last_seen: datetime | None
    authorization_status: str

    model_config = {"from_attributes": True}


class EngineHealth(BaseModel):
    score: float
    rpm: float | None
    temperature_c: float | None
    oil_pressure_psi: float | None
    coolant_temperature_c: float | None
    hours: float
    fault_codes: list[str]


class FuelHealth(BaseModel):
    score: float
    level_pct: float | None
    consumption_rate_lph: float | None
    efficiency_score: float


class HydraulicsHealth(BaseModel):
    score: float
    pressure_bar: float | None
    temperature_c: float | None
    flow_lpm: float | None


class ElectricalHealth(BaseModel):
    score: float
    battery_voltage: float | None


class MechanicalHealth(BaseModel):
    score: float
    vibration_g: float | None
    brake_status: str
    track_condition: str


class MaintenanceHealth(BaseModel):
    score: float
    last_service_days_ago: int | None
    next_service_due_hours: float | None
    status: str


class MachineHealthResponse(BaseModel):
    machine_id: str
    machine_code: str
    overall_health: float
    components: dict[str, Any]
    active_faults: list[str]
    maintenance_risk: str  # LOW|MEDIUM|HIGH
    computed_at: str
