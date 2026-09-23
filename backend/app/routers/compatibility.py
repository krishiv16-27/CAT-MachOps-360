"""
Operator-Machine Compatibility Score router.
GET /api/v1/compatibility?operator_id=&machine_id=&task_type=
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.database import get_db
from ..core.dependencies import get_current_user
from ..schemas.common import ApiResponse

router = APIRouter()


@router.get("")
async def get_compatibility(
    operator_id: str = Query(...),
    machine_id: str = Query(...),
    task_type: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """
    Returns an operator-machine compatibility score (0–100) with component breakdown.
    """
    from ..services.compatibility import get_compatibility_score
    result = await get_compatibility_score(operator_id, machine_id, task_type, db)
    return ApiResponse(data=result)
