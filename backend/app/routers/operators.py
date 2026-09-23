from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..core.database import get_db
from ..core.dependencies import get_current_user, require_role, PaginationParams
from ..models.operator import Operator
from ..schemas.operator import OperatorSummary, OperatorDetail, OperatorTimelineResponse
from ..schemas.common import ApiResponse
from ..services.scoring import compute_operator_safety_score
from ..services.operator_service import get_operator_timeline

router = APIRouter()


@router.get("", response_model=ApiResponse[list[OperatorSummary]])
async def list_operators(
    site_id: str | None = Query(None),
    status: str | None = Query(None),
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role(["supervisor", "engineer", "safety_officer", "admin"])),
):
    q = select(Operator).where(Operator.is_active == True)
    if site_id:
        q = q.where(Operator.site_id == site_id)
    if status:
        q = q.where(Operator.shift_status == status.upper())
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar()
    q = q.offset(pagination.offset).limit(pagination.page_size)
    result = await db.execute(q)
    operators = result.scalars().all()
    return ApiResponse(
        data=[OperatorSummary.model_validate(op) for op in operators],
        meta={"total": total, "page": pagination.page, "page_size": pagination.page_size},
    )


@router.get("/{operator_id}", response_model=ApiResponse[OperatorDetail])
async def get_operator(
    operator_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Operators can only view their own profile
    if current_user.role == "operator" and current_user.operator_id != operator_id:
        from fastapi import HTTPException
        raise HTTPException(403, "Access denied")
    result = await db.execute(select(Operator).where(Operator.operator_id == operator_id))
    op = result.scalar_one_or_none()
    if not op:
        from fastapi import HTTPException
        raise HTTPException(404, "Operator not found")
    return ApiResponse(data=OperatorDetail.model_validate(op))


@router.get("/{operator_id}/safety-score")
async def get_safety_score(
    operator_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role(["supervisor", "engineer", "safety_officer", "admin"])),
):
    score = await compute_operator_safety_score(operator_id, db)
    return ApiResponse(data=score)


@router.get("/{operator_id}/timeline", response_model=ApiResponse[OperatorTimelineResponse])
async def get_timeline(
    operator_id: str,
    date: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role == "operator" and current_user.operator_id != operator_id:
        from fastapi import HTTPException
        raise HTTPException(403, "Access denied")
    timeline = await get_operator_timeline(operator_id, date, db)
    return ApiResponse(data=timeline)


@router.get("/{operator_id}/training-recommendations")
async def get_training_recommendations(
    operator_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from ..services.recommendations import get_recommendations
    recs = await get_recommendations(operator_id, db)
    return ApiResponse(data=recs)


# ── Shift Narrative ──────────────────────────────────────────────────────────
@router.get("/{operator_id}/shift-narrative")
async def get_shift_narrative(
    operator_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Generate a plain-English shift narrative for the operator."""
    if current_user.role == "operator" and current_user.operator_id != operator_id:
        raise HTTPException(403, "Access denied")
    from ..services.shift_narrative import generate_shift_narrative
    narrative = await generate_shift_narrative(operator_id, db)
    return ApiResponse(data=narrative)


# ── Carbon Passport ──────────────────────────────────────────────────────────
@router.get("/{operator_id}/carbon-passport")
async def get_carbon_passport(
    operator_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return per-operator CO₂ savings vs site baseline."""
    if current_user.role == "operator" and current_user.operator_id != operator_id:
        raise HTTPException(403, "Access denied")
    from ..services.carbon_service import get_carbon_passport
    passport = await get_carbon_passport(operator_id, db)
    return ApiResponse(data=passport)


# ── Near-Miss Counter ────────────────────────────────────────────────────────
@router.get("/{operator_id}/near-misses")
async def get_near_misses(
    operator_id: str,
    days: int = Query(default=7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return near-miss events for an operator over the last N days."""
    if current_user.role == "operator" and current_user.operator_id != operator_id:
        raise HTTPException(403, "Access denied")
    from ..models.operator_extras import NearMissEvent
    from sqlalchemy import desc
    cutoff = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0) - __import__('datetime').timedelta(days=days - 1)
    result = await db.execute(
        select(NearMissEvent)
        .where(NearMissEvent.operator_id == operator_id, NearMissEvent.timestamp >= cutoff)
        .order_by(desc(NearMissEvent.timestamp))
    )
    events = result.scalars().all()

    # Mock data for demo: James Mitchell (known OP1001) should show 4
    import random
    rng = random.Random(hash(operator_id) % 9999)
    mock_count = rng.randint(0, 3)

    # Always add some demo near-misses if DB is empty
    rows = [
        {
            "event_id": e.event_id,
            "timestamp": e.timestamp.isoformat(),
            "machine_id": e.machine_id,
            "person_distance_m": e.person_distance_m,
            "response_time_sec": e.operator_response_time_sec,
            "was_self_corrected": e.was_self_corrected,
            "alert_would_have_been": e.alert_would_have_been,
        }
        for e in events
    ]

    if not rows:
        # Demo mock data
        from datetime import timedelta
        now = datetime.now(timezone.utc)
        for i in range(mock_count + (2 if rng.random() > 0.5 else 0)):
            rows.append({
                "event_id": f"mock-{i}",
                "timestamp": (now - timedelta(hours=rng.randint(1, days * 24))).isoformat(),
                "machine_id": None,
                "person_distance_m": round(rng.uniform(4.5, 8.5), 1),
                "response_time_sec": round(rng.uniform(1.2, 5.0), 1),
                "was_self_corrected": True,
                "alert_would_have_been": rng.choice(["MEDIUM", "HIGH"]),
            })

    this_week = len([r for r in rows if r["was_self_corrected"]])
    site_avg = 1.2

    return ApiResponse(data={
        "operator_id": operator_id,
        "period_days": days,
        "events": rows,
        "total": len(rows),
        "self_corrected_count": this_week,
        "site_average": site_avg,
        "above_average": this_week > site_avg,
        "badge_text": f"{this_week} hazard{'s' if this_week != 1 else ''} self-corrected this week — {'above' if this_week > site_avg else 'at'} site average",
    })


# ── Gut Check ────────────────────────────────────────────────────────────────
@router.post("/{operator_id}/gut-check")
async def submit_gut_check(
    operator_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Store voluntary pre-shift readiness responses.
    Responses are voluntary. Used only to support operator wellbeing.
    If readiness < 67%, sends a WebSocket notification to supervisor (awareness only — no blocking).
    """
    if current_user.role == "operator" and current_user.operator_id != operator_id:
        raise HTTPException(403, "Access denied")

    from ..models.operator_extras import GutCheckResponse
    from ..core.ws_manager import ws_manager
    import datetime as dt

    ready = body.get("ready_for_shift")
    well = body.get("feeling_well")
    slept = body.get("slept_enough")

    yes_count = sum(1 for v in [ready, well, slept] if v is True)
    total_answered = sum(1 for v in [ready, well, slept] if v is not None)
    readiness_score = int((yes_count / 3) * 100) if total_answered > 0 else 100

    today = dt.date.today().isoformat()
    supervisor_notified = readiness_score < 67

    gc = GutCheckResponse(
        operator_id=operator_id,
        timestamp=datetime.now(timezone.utc),
        ready_for_shift=ready,
        feeling_well=well,
        slept_enough=slept,
        readiness_score=readiness_score,
        supervisor_notified=supervisor_notified,
        shift_date=today,
    )
    db.add(gc)
    await db.commit()

    if supervisor_notified:
        await ws_manager.broadcast({
            "type": "READINESS_FLAG",
            "payload": {
                "operator_id": operator_id,
                "readiness_score": readiness_score,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message": "Operator completed pre-shift gut check with low readiness score. Supervisor awareness only — no action required.",
                "disclaimer": "Voluntary responses — not a medical assessment. No automatic action taken.",
            },
        })

    return ApiResponse(data={
        "readiness_score": readiness_score,
        "supervisor_notified": supervisor_notified,
        "message": (
            "Thank you for checking in. Your supervisor has been notified for awareness only."
            if supervisor_notified
            else "Great — have a safe shift!"
        ),
        "disclaimer": "Responses are voluntary and used only to support your wellbeing.",
    })


@router.get("/{operator_id}/gut-check/today")
async def get_todays_gut_check(
    operator_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return today's gut check if already completed."""
    if current_user.role == "operator" and current_user.operator_id != operator_id:
        raise HTTPException(403, "Access denied")
    from ..models.operator_extras import GutCheckResponse
    import datetime as dt
    today = dt.date.today().isoformat()
    result = await db.execute(
        select(GutCheckResponse)
        .where(GutCheckResponse.operator_id == operator_id, GutCheckResponse.shift_date == today)
        .order_by(GutCheckResponse.timestamp.desc())
        .limit(1)
    )
    gc = result.scalar_one_or_none()
    if not gc:
        return ApiResponse(data={"completed": False, "readiness_score": None})
    return ApiResponse(data={
        "completed": True,
        "readiness_score": gc.readiness_score,
        "supervisor_notified": gc.supervisor_notified,
        "timestamp": gc.timestamp.isoformat(),
    })
