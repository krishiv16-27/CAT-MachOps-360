from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime, timezone
from ..core.database import get_db
from ..core.dependencies import get_current_user, require_role, PaginationParams
from ..models.safety import DashcamEvent
from ..schemas.common import ApiResponse

router = APIRouter()


@router.get("/events")
async def list_cv_events(
    machine_id: str | None = Query(None),
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    q = select(DashcamEvent).order_by(desc(DashcamEvent.timestamp))
    if machine_id:
        q = q.where(DashcamEvent.machine_id == machine_id)
    q = q.offset(pagination.offset).limit(pagination.page_size)
    result = await db.execute(q)
    events = result.scalars().all()
    data = [
        {
            "event_id": e.event_id,
            "timestamp": e.timestamp.isoformat(),
            "camera_id": e.camera_id,
            "machine_id": e.machine_id,
            "event_type": e.event_type,
            "person_detected": e.person_detected,
            "vehicle_detected": e.vehicle_detected,
            "obstacle_detected": e.obstacle_detected,
            "restricted_zone_entry": e.restricted_zone_entry,
            "estimated_distance_m": e.estimated_distance_m,
            "confidence": e.confidence,
        }
        for e in events
    ]
    return ApiResponse(data=data)


@router.post("/simulate")
async def simulate_cv_event(
    body: dict,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role(["engineer", "supervisor", "admin"])),
):
    """Inject a simulated CV event for demo purposes."""
    from ..services.safety_engine import SafetyEngine
    from ..core.ws_manager import ws_manager

    event_type = body.get("event_type", "person_detected")
    machine_id = body.get("machine_id", "")
    distance_m = body.get("distance_m", 4.0)

    cv_event = DashcamEvent(
        timestamp=datetime.now(timezone.utc),
        camera_id=f"CAM-{machine_id[:8] if machine_id else 'SIM'}-FRONT",
        machine_id=machine_id or "SIM001",
        operator_id=body.get("operator_id"),
        person_detected=event_type == "person_detected",
        vehicle_detected=event_type == "vehicle_detected",
        obstacle_detected=event_type == "obstacle_detected",
        restricted_zone_entry=event_type == "restricted_zone_entry",
        estimated_distance_m=distance_m,
        confidence=0.87,
        event_type=event_type,
        raw_metadata={"source": "simulated", "scenario": "demo"},
    )
    db.add(cv_event)
    await db.flush()

    # Run through safety engine
    engine = SafetyEngine()
    alerts = await engine.evaluate_cv_event(cv_event, db)

    return ApiResponse(data={
        "event_id": cv_event.event_id,
        "event_type": event_type,
        "alerts_created": len(alerts),
        "alerts": [a.alert_id for a in alerts],
    })


@router.get("/cameras")
async def list_cameras(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    from ..models.machine import Machine
    result = await db.execute(select(Machine).where(Machine.is_active == True, Machine.status == "ACTIVE"))
    machines = result.scalars().all()
    cameras = [
        {
            "camera_id": f"CAM-{m.machine_code}-FRONT",
            "machine_id": m.machine_id,
            "machine_code": m.machine_code,
            "status": "LIVE_SIM",
            "location": "Front-facing",
        }
        for m in machines
    ]
    return ApiResponse(data=cameras)
