from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..core.database import get_db
from ..core.dependencies import get_current_user, require_role, PaginationParams
from ..models.machine import Machine, MachineModel
from ..schemas.machine import MachineSummary, MachineHealthResponse
from ..schemas.common import ApiResponse
from ..services.machine_health import compute_machine_health

router = APIRouter()


@router.get("", response_model=ApiResponse[list[MachineSummary]])
async def list_machines(
    site_id: str | None = Query(None),
    status: str | None = Query(None),
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    q = select(Machine).where(Machine.is_active == True)
    if site_id:
        q = q.where(Machine.site_id == site_id)
    if status:
        q = q.where(Machine.status == status.upper())
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar()
    q = q.offset(pagination.offset).limit(pagination.page_size)
    result = await db.execute(q)
    machines = result.scalars().all()

    summaries = []
    for m in machines:
        summaries.append(MachineSummary(
            machine_id=m.machine_id,
            machine_code=m.machine_code,
            machine_type=m.model.machine_type if m.model else "UNKNOWN",
            model_name=m.model.model_name if m.model else "Unknown",
            site_id=m.site_id,
            zone_id=m.zone_id,
            status=m.status,
            current_operator_id=m.current_operator_id,
            current_task_id=m.current_task_id,
            engine_hours=m.engine_hours,
            last_fuel_level_pct=m.last_fuel_level_pct,
            last_engine_temp_c=m.last_engine_temp_c,
            last_health_score=m.last_health_score,
            last_seen=m.last_seen,
            authorization_status=m.authorization_status,
        ))
    return ApiResponse(data=summaries, meta={"total": total})


@router.get("/{machine_id}", response_model=ApiResponse[MachineSummary])
async def get_machine(
    machine_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(select(Machine).where(Machine.machine_id == machine_id))
    m = result.scalar_one_or_none()
    if not m:
        raise HTTPException(404, "Machine not found")
    return ApiResponse(data=MachineSummary(
        machine_id=m.machine_id,
        machine_code=m.machine_code,
        machine_type=m.model.machine_type if m.model else "UNKNOWN",
        model_name=m.model.model_name if m.model else "Unknown",
        site_id=m.site_id,
        zone_id=m.zone_id,
        status=m.status,
        current_operator_id=m.current_operator_id,
        current_task_id=m.current_task_id,
        engine_hours=m.engine_hours,
        last_fuel_level_pct=m.last_fuel_level_pct,
        last_engine_temp_c=m.last_engine_temp_c,
        last_health_score=m.last_health_score,
        last_seen=m.last_seen,
        authorization_status=m.authorization_status,
    ))


@router.get("/{machine_id}/health", response_model=ApiResponse[MachineHealthResponse])
async def get_machine_health(
    machine_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    health = await compute_machine_health(machine_id, db)
    return ApiResponse(data=health)


@router.get("/{machine_id}/telemetry")
async def get_machine_telemetry(
    machine_id: str,
    from_ts: str | None = Query(None),
    to_ts: str | None = Query(None),
    limit: int = Query(default=100, le=1000),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    from ..models.telemetry import Telemetry
    from sqlalchemy import desc
    q = select(Telemetry).where(Telemetry.machine_id == machine_id).order_by(desc(Telemetry.timestamp)).limit(limit)
    result = await db.execute(q)
    rows = result.scalars().all()
    data = [
        {
            "timestamp": r.timestamp.isoformat(),
            "engine_rpm": r.engine_rpm,
            "engine_temperature_c": r.engine_temperature_c,
            "fuel_level_pct": r.fuel_level_pct,
            "machine_load_pct": r.machine_load_pct,
            "machine_speed_kmh": r.machine_speed_kmh,
            "hydraulic_pressure_bar": r.hydraulic_pressure_bar,
            "idle_time_min": r.idle_time_min,
            "seatbelt_status": r.seatbelt_status,
        }
        for r in rows
    ]
    return ApiResponse(data=data, meta={"total": len(data)})


@router.get("/{machine_id}/silent-risk")
async def get_silent_risk(
    machine_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Composite weak-signal risk detection for a machine (last 30 min telemetry)."""
    from ..services.silent_risk import get_silent_risk
    risk = await get_silent_risk(machine_id, db)
    return ApiResponse(data=risk)


@router.get("/{machine_id}/machine-speaks")
async def get_machine_speaks(
    machine_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """First-person machine status message — template-based, updates every 30s."""
    from datetime import datetime, timezone, timedelta
    from sqlalchemy import desc
    from ..models.telemetry import Telemetry
    from ..models.machine import MachineMaintenance
    from ..services.machine_health import compute_machine_health

    result = await db.execute(select(Machine).where(Machine.machine_id == machine_id))
    m = result.scalar_one_or_none()
    if not m:
        raise HTTPException(404, "Machine not found")

    health = await compute_machine_health(machine_id, db)

    # Latest telemetry
    telem_result = await db.execute(
        select(Telemetry).where(Telemetry.machine_id == machine_id)
        .order_by(desc(Telemetry.timestamp)).limit(5)
    )
    recent = telem_result.scalars().all()

    # Last maintenance
    maint_result = await db.execute(
        select(MachineMaintenance).where(MachineMaintenance.machine_id == machine_id)
        .order_by(desc(MachineMaintenance.performed_at)).limit(1)
    )
    last_maint = maint_result.scalar_one_or_none()
    days_since_service = None
    if last_maint:
        performed = last_maint.performed_at
        if performed.tzinfo is None:
            from datetime import timezone as _tz
            performed = performed.replace(tzinfo=_tz.utc)
        delta = datetime.now(timezone.utc) - performed
        days_since_service = delta.days

    temp = m.last_engine_temp_c or (recent[0].engine_temperature_c if recent else 90)
    fuel = m.last_fuel_level_pct or (recent[0].fuel_level_pct if recent else 60)
    overall = health.overall_health if health else 85

    # Hydraulic trend — is it rising?
    hydr_temps = [r.hydraulic_temperature_c for r in recent if r.hydraulic_temperature_c]
    hydr_rising = len(hydr_temps) >= 3 and hydr_temps[0] > hydr_temps[-1]  # desc order → [0] is latest
    hydr_current = hydr_temps[0] if hydr_temps else None

    # Hours until fuel empty (rough estimate)
    fuel_rate = recent[0].fuel_consumption_rate_lph if recent and recent[0].fuel_consumption_rate_lph else 12.0
    hours_of_fuel = (fuel / 100 * 500) / max(fuel_rate, 0.1)  # 500L tank approx

    # Build message
    active_faults = health.active_faults if health else []
    if overall > 90 and not active_faults:
        message = (
            f"I'm running well today. Engine at {temp:.0f}°C, fuel at {fuel:.0f}%, "
            f"{m.engine_hours:.0f} hours logged. Nothing concerning to report."
        )
        tone = "good"
    elif hydr_rising and hydr_current and hydr_current > 58:
        n_mins = len(hydr_temps)
        svc_note = f"Last full service was {days_since_service} days ago." if days_since_service else ""
        message = (
            f"I've been noticing my hydraulic temperature climbing for the last {n_mins} readings — "
            f"currently at {hydr_current:.0f}°C. Not critical yet, but I'd appreciate a load reduction. {svc_note}"
        )
        tone = "warning"
    elif fuel < 20:
        message = (
            f"My fuel is getting low — {fuel:.0f}% remaining, approximately {hours_of_fuel:.1f} hours "
            f"of operation left at current consumption rate. A refuel before the next task would keep the shift running smoothly."
        )
        tone = "warning"
    elif overall < 75:
        top_concerns = []
        if health:
            comps = health.components
            for k in ('engine', 'hydraulics', 'fuel', 'mechanical'):
                comp = getattr(comps, k, None)
                if comp and comp.score < 75:
                    top_concerns.append(f"{k} ({comp.score:.0f}%)")
        concerns_text = " and ".join(top_concerns[:2]) if top_concerns else "multiple systems"
        message = (
            f"I'm not feeling my best today. {concerns_text} need attention. "
            f"I'd recommend a maintenance review before extended operation."
        )
        tone = "critical"
    else:
        message = (
            f"All systems normal. Engine at {temp:.0f}°C, load at {m.last_machine_load_pct or 50:.0f}%, "
            f"fuel at {fuel:.0f}%. Ready for the next task."
        )
        tone = "good"

    return ApiResponse(data={
        "machine_id": machine_id,
        "machine_code": m.machine_code,
        "message": message,
        "tone": tone,  # good | warning | critical
        "metrics": {
            "engine_temp_c": round(temp, 1),
            "fuel_level_pct": round(fuel, 1),
            "overall_health": round(float(overall), 1),
            "hours_of_fuel_remaining": round(hours_of_fuel, 1),
            "hydraulic_temp_rising": hydr_rising,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    })
