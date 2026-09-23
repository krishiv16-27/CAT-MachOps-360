from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from ..core.database import get_db
from ..core.dependencies import get_current_user, require_role
from ..models.machine import Machine
from ..models.operator import Operator
from ..models.task import Task
from ..models.safety import Alert, Incident
from ..schemas.common import ApiResponse
from datetime import datetime, timezone, date

router = APIRouter()


@router.get("/site-overview")
async def site_overview(
    site_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Returns the 7 KPI card values for the dashboard."""
    today = date.today()

    # Machines active
    total_machines = (await db.execute(select(func.count()).where(Machine.is_active == True))).scalar()
    active_machines = (await db.execute(
        select(func.count()).where(Machine.status == "ACTIVE", Machine.is_active == True)
    )).scalar()

    # Operators active
    total_ops = (await db.execute(select(func.count()).where(Operator.is_active == True))).scalar()
    active_ops = (await db.execute(
        select(func.count()).where(Operator.shift_status == "ON_SHIFT", Operator.is_active == True)
    )).scalar()

    # Active alerts (unresolved)
    active_alerts = (await db.execute(
        select(func.count()).where(Alert.resolved == False)
    )).scalar()

    # Incidents today
    incidents_today = (await db.execute(
        select(func.count()).where(
            func.date(Alert.timestamp) == today,
        )
    )).scalar()

    # Avg health score
    health_result = await db.execute(
        select(func.avg(Machine.last_health_score)).where(
            Machine.last_health_score.isnot(None),
            Machine.is_active == True,
        )
    )
    avg_health = health_result.scalar() or 94.0

    # Avg safety score
    safety_result = await db.execute(
        select(func.avg(Operator.safety_score)).where(Operator.is_active == True)
    )
    avg_safety = safety_result.scalar() or 91.0

    # Productivity — tasks completed today / total assigned today
    tasks_today = (await db.execute(
        select(func.count()).where(
            func.date(Task.actual_start) == today
        )
    )).scalar() or 1

    tasks_completed_today = (await db.execute(
        select(func.count()).where(
            func.date(Task.actual_start) == today,
            Task.status == "COMPLETED",
        )
    )).scalar() or 0

    productivity = round((tasks_completed_today / max(tasks_today, 1)) * 100, 1)

    return ApiResponse(data={
        "machines_active": active_machines,
        "machines_total": total_machines,
        "operators_active": active_ops,
        "operators_total": total_ops,
        "safety_score": round(float(avg_safety), 1),
        "machine_health": round(float(avg_health), 1),
        "productivity": productivity,
        "active_alerts": active_alerts,
        "incidents_today": incidents_today,
        "as_of": datetime.now(timezone.utc).isoformat(),
    })


@router.get("/productivity")
async def productivity_analytics(
    site_id: str | None = Query(None),
    from_ts: str | None = Query(None),
    to_ts: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role(["supervisor", "engineer", "admin"])),
):
    q = select(Task).where(Task.status.in_(["COMPLETED", "IN_PROGRESS"]))
    if site_id:
        q = q.where(Task.site_id == site_id)
    result = await db.execute(q)
    tasks = result.scalars().all()

    completed = [t for t in tasks if t.status == "COMPLETED"]
    total = len(tasks)
    completion_rate = round(len(completed) / max(total, 1) * 100, 1)

    durations = [t.actual_duration_minutes for t in completed if t.actual_duration_minutes]
    avg_actual = sum(durations) / len(durations) if durations else 0

    estimated = [t.estimated_duration_minutes for t in completed if t.estimated_duration_minutes and t.actual_duration_minutes]
    eta_accuracy = 0.0
    if estimated:
        accuracies = []
        for t in completed:
            if t.estimated_duration_minutes and t.actual_duration_minutes and t.estimated_duration_minutes > 0:
                acc = 1 - abs(t.actual_duration_minutes - t.estimated_duration_minutes) / t.estimated_duration_minutes
                accuracies.append(max(0, acc) * 100)
        eta_accuracy = round(sum(accuracies) / len(accuracies), 1) if accuracies else 0.0

    return ApiResponse(data={
        "tasks_total": total,
        "tasks_completed": len(completed),
        "completion_rate_pct": completion_rate,
        "avg_actual_duration_minutes": round(avg_actual, 1),
        "eta_accuracy_pct": eta_accuracy,
        "material_moved_m3": round(sum(t.completed_quantity for t in completed if t.completed_quantity), 1),
    })
