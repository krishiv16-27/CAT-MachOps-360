from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime, timezone
from ..core.database import get_db
from ..core.dependencies import get_current_user, require_role, PaginationParams
from ..models.safety import Incident
from ..schemas.alert import IncidentOut, IncidentCreate
from ..schemas.common import ApiResponse

router = APIRouter()


@router.get("", response_model=ApiResponse[list[IncidentOut]])
async def list_incidents(
    site_id: str | None = Query(None),
    operator_id: str | None = Query(None),
    machine_id: str | None = Query(None),
    status: str | None = Query(None),
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    q = select(Incident).order_by(desc(Incident.timestamp))
    if operator_id:
        q = q.where(Incident.operator_id == operator_id)
    if machine_id:
        q = q.where(Incident.machine_id == machine_id)
    if site_id:
        q = q.where(Incident.site_id == site_id)
    if status:
        q = q.where(Incident.status == status.upper())
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar()
    q = q.offset(pagination.offset).limit(pagination.page_size)
    result = await db.execute(q)
    incidents = result.scalars().all()
    return ApiResponse(data=[IncidentOut.model_validate(i) for i in incidents], meta={"total": total})


@router.get("/{incident_id}", response_model=ApiResponse[IncidentOut])
async def get_incident(incident_id: str, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(Incident).where(Incident.incident_id == incident_id))
    inc = result.scalar_one_or_none()
    if not inc:
        raise HTTPException(404, "Incident not found")
    return ApiResponse(data=IncidentOut.model_validate(inc))


@router.post("", response_model=ApiResponse[IncidentOut])
async def create_incident(
    body: IncidentCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    inc = Incident(
        timestamp=datetime.now(timezone.utc),
        **body.model_dump(),
    )
    db.add(inc)
    await db.flush()
    return ApiResponse(data=IncidentOut.model_validate(inc))


@router.patch("/{incident_id}")
async def update_incident(
    incident_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role(["supervisor", "engineer", "safety_officer", "admin"])),
):
    result = await db.execute(select(Incident).where(Incident.incident_id == incident_id))
    inc = result.scalar_one_or_none()
    if not inc:
        raise HTTPException(404, "Incident not found")
    for k, v in body.items():
        if hasattr(inc, k):
            setattr(inc, k, v)
    if body.get("status") == "RESOLVED":
        inc.resolved_at = datetime.now(timezone.utc)
    return ApiResponse(data=IncidentOut.model_validate(inc))
