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
