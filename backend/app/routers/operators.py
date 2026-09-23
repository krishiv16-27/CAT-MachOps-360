from fastapi import APIRouter, Depends, Query
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
