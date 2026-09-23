from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..core.database import get_db
from ..core.dependencies import get_current_user, require_role
from ..models.training import TrainingModule, OperatorTraining
from ..schemas.common import ApiResponse

router = APIRouter()


@router.get("/modules")
async def list_modules(
    category: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    q = select(TrainingModule).where(TrainingModule.is_active == True)
    if category:
        q = q.where(TrainingModule.category == category.upper())
    result = await db.execute(q)
    modules = result.scalars().all()
    return ApiResponse(data=[
        {
            "module_id": m.module_id,
            "title": m.title,
            "description": m.description,
            "category": m.category,
            "module_type": m.module_type,
            "duration_minutes": m.duration_minutes,
            "is_mandatory": m.is_mandatory,
        }
        for m in modules
    ])


@router.get("/operator/{operator_id}")
async def operator_training_status(
    operator_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role == "operator" and current_user.operator_id != operator_id:
        from fastapi import HTTPException
        raise HTTPException(403, "Access denied")
    result = await db.execute(
        select(OperatorTraining).where(OperatorTraining.operator_id == operator_id)
    )
    records = result.scalars().all()
    return ApiResponse(data=[
        {
            "record_id": r.record_id,
            "module_id": r.module_id,
            "status": r.status,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            "score": r.score,
        }
        for r in records
    ])
