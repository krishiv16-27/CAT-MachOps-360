"""
Deterministic machine health score computation.
No ML — weighted formula from telemetry and maintenance records.
"""
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from ..core.config import settings
from ..models.machine import Machine, MachineFault, MachineMaintenance
from ..models.telemetry import Telemetry
from ..schemas.machine import MachineHealthResponse
import logging

logger = logging.getLogger(__name__)


def _score_engine(rpm, temp_c, oil_psi, hours, faults) -> tuple[float, dict]:
    score = 100.0
    detail = {}
    if temp_c:
        if temp_c > settings.engine_temp_critical_c:
            score -= 40
        elif temp_c > settings.engine_temp_warning_c:
            score -= 15
        detail["temperature_c"] = temp_c
    if oil_psi:
        if oil_psi < 25:
            score -= 30
        elif oil_psi < 35:
            score -= 10
        detail["oil_pressure_psi"] = oil_psi
    if faults:
        score -= min(len(faults) * 10, 30)
    detail["fault_count"] = len(faults)
    detail["hours"] = hours
    return max(0.0, score), detail


def _score_fuel(level_pct, consumption_rate) -> tuple[float, dict]:
    score = 100.0
    if level_pct is not None:
        if level_pct < 10:
            score -= 30
        elif level_pct < 20:
            score -= 15
        elif level_pct < 30:
            score -= 5
    efficiency_score = 80.0  # baseline — would improve with historical data
    return max(0.0, score), {"level_pct": level_pct, "consumption_rate_lph": consumption_rate, "efficiency_score": efficiency_score}


def _score_hydraulics(pressure_bar, temp_c, flow_lpm) -> tuple[float, dict]:
    score = 100.0
    if pressure_bar:
        nominal = 250.0
        deviation = abs(pressure_bar - nominal) / nominal
        if deviation > 0.3:
            score -= 30
        elif deviation > 0.2:
            score -= 15
        elif deviation > 0.1:
            score -= 5
    return max(0.0, score), {"pressure_bar": pressure_bar, "temperature_c": temp_c, "flow_lpm": flow_lpm}


def _score_electrical(battery_v) -> tuple[float, dict]:
    score = 100.0
    if battery_v:
        if battery_v < 11.5:
            score -= 40
        elif battery_v < 12.0:
            score -= 15
        elif battery_v > 15.0:
            score -= 10
    return max(0.0, score), {"battery_voltage": battery_v}


def _score_mechanical(vibration_g) -> tuple[float, dict]:
    score = 100.0
    if vibration_g:
        if vibration_g > 2.0:
            score -= 30
        elif vibration_g > 1.0:
            score -= 15
    return max(0.0, score), {
        "vibration_g": vibration_g,
        "brake_status": "OK",
        "track_condition": "GOOD",
        "transmission_status": "OK",
    }


def _score_maintenance(last_service_days, next_service_hours_remaining) -> tuple[float, dict]:
    score = 100.0
    risk = "LOW"
    if next_service_hours_remaining is not None:
        if next_service_hours_remaining < 0:
            score -= 30
            risk = "HIGH"
        elif next_service_hours_remaining < 50:
            score -= 15
            risk = "MEDIUM"
        elif next_service_hours_remaining < 100:
            score -= 5
            risk = "LOW"
    return max(0.0, score), {
        "last_service_days_ago": last_service_days,
        "next_service_due_hours": next_service_hours_remaining,
        "status": "OVERDUE" if (next_service_hours_remaining or 999) < 0 else "OK",
        "risk": risk,
    }


async def compute_machine_health(machine_id: str, db: AsyncSession) -> MachineHealthResponse:
    # Fetch machine
    m_result = await db.execute(select(Machine).where(Machine.machine_id == machine_id))
    machine = m_result.scalar_one_or_none()
    if not machine:
        raise ValueError(f"Machine {machine_id} not found")

    # Latest telemetry
    telem_result = await db.execute(
        select(Telemetry)
        .where(Telemetry.machine_id == machine_id)
        .order_by(desc(Telemetry.timestamp))
        .limit(1)
    )
    telem = telem_result.scalar_one_or_none()

    # Active faults
    faults_result = await db.execute(
        select(MachineFault).where(MachineFault.machine_id == machine_id, MachineFault.is_active == True)
    )
    faults = faults_result.scalars().all()
    fault_codes = [f.fault_code for f in faults]

    # Latest maintenance
    maint_result = await db.execute(
        select(MachineMaintenance)
        .where(MachineMaintenance.machine_id == machine_id)
        .order_by(desc(MachineMaintenance.performed_at))
        .limit(1)
    )
    last_maint = maint_result.scalar_one_or_none()

    last_service_days = None
    next_service_remaining = None
    if last_maint:
        days = (datetime.now(timezone.utc) - last_maint.performed_at).days
        last_service_days = days
        if last_maint.next_service_hours and machine.engine_hours:
            next_service_remaining = last_maint.next_service_hours - machine.engine_hours

    # Compute component scores
    engine_score, engine_detail = _score_engine(
        telem.engine_rpm if telem else None,
        telem.engine_temperature_c if telem else None,
        telem.oil_pressure_psi if telem else None,
        machine.engine_hours,
        faults,
    )
    fuel_score, fuel_detail = _score_fuel(
        telem.fuel_level_pct if telem else None,
        telem.fuel_consumption_rate_lph if telem else None,
    )
    hydraulic_score, hydraulic_detail = _score_hydraulics(
        telem.hydraulic_pressure_bar if telem else None,
        telem.hydraulic_temperature_c if telem else None,
        telem.hydraulic_flow_lpm if telem else None,
    )
    electrical_score, electrical_detail = _score_electrical(telem.battery_voltage if telem else None)
    mechanical_score, mechanical_detail = _score_mechanical(telem.vibration_g if telem else None)
    maintenance_score, maintenance_detail = _score_maintenance(last_service_days, next_service_remaining)

    # Overall weighted score
    s = settings
    overall = (
        engine_score * s.health_weight_engine
        + fuel_score * s.health_weight_fuel
        + hydraulic_score * s.health_weight_hydraulics
        + electrical_score * s.health_weight_electrical
        + mechanical_score * s.health_weight_mechanical
        + maintenance_score * s.health_weight_maintenance
    )

    # Determine maintenance risk
    if maintenance_detail["risk"] == "HIGH" or any(f.severity == "CRITICAL" for f in faults):
        maint_risk = "HIGH"
    elif maintenance_detail["risk"] == "MEDIUM" or len(faults) > 0:
        maint_risk = "MEDIUM"
    else:
        maint_risk = "LOW"

    # Update cached value on machine
    machine.last_health_score = round(overall, 1)

    return MachineHealthResponse(
        machine_id=machine_id,
        machine_code=machine.machine_code,
        overall_health=round(overall, 1),
        components={
            "engine": {**engine_detail, "score": round(engine_score, 1)},
            "fuel": {**fuel_detail, "score": round(fuel_score, 1)},
            "hydraulics": {**hydraulic_detail, "score": round(hydraulic_score, 1)},
            "electrical": {**electrical_detail, "score": round(electrical_score, 1)},
            "mechanical": {**mechanical_detail, "score": round(mechanical_score, 1)},
            "maintenance": {**maintenance_detail, "score": round(maintenance_score, 1)},
        },
        active_faults=fault_codes,
        maintenance_risk=maint_risk,
        computed_at=datetime.now(timezone.utc).isoformat(),
    )
