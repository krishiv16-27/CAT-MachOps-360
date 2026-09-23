from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime, timezone
from ..core.database import get_db
from ..core.dependencies import get_current_user, PaginationParams
from ..models.safety import Alert
from ..schemas.alert import AlertOut, AcknowledgeRequest
from ..schemas.common import ApiResponse
from ..core.ws_manager import ws_manager

router = APIRouter()


@router.get("", response_model=ApiResponse[list[AlertOut]])
async def list_alerts(
    severity: str | None = Query(None),
    resolved: bool | None = Query(None),
    machine_id: str | None = Query(None),
    operator_id: str | None = Query(None),
    from_ts: str | None = Query(None),
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = select(Alert).order_by(desc(Alert.timestamp))
    if current_user.role == "operator":
        q = q.where(Alert.operator_id == current_user.operator_id)
    else:
        if machine_id:
            q = q.where(Alert.machine_id == machine_id)
        if operator_id:
            q = q.where(Alert.operator_id == operator_id)
    if severity:
        q = q.where(Alert.severity == severity.upper())
    if resolved is not None:
        q = q.where(Alert.resolved == resolved)
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar()
    q = q.offset(pagination.offset).limit(pagination.page_size)
    result = await db.execute(q)
    alerts = result.scalars().all()
    return ApiResponse(data=[AlertOut.model_validate(a) for a in alerts], meta={"total": total})


@router.get("/{alert_id}", response_model=ApiResponse[AlertOut])
async def get_alert(alert_id: str, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(Alert).where(Alert.alert_id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(404, "Alert not found")
    return ApiResponse(data=AlertOut.model_validate(alert))


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    body: AcknowledgeRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Alert).where(Alert.alert_id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(404, "Alert not found")
    alert.acknowledged = True
    alert.acknowledged_by = current_user.user_id
    alert.acknowledged_at = datetime.now(timezone.utc)
    alert.acknowledgement_note = body.note
    # Broadcast acknowledgement
    await ws_manager.broadcast({
        "type": "ALERT_ACKNOWLEDGED",
        "payload": {
            "alert_id": alert_id,
            "acknowledged_by": current_user.user_id,
            "acknowledged_at": alert.acknowledged_at.isoformat(),
        },
    })
    return ApiResponse(data={"alert_id": alert_id, "acknowledged": True})
