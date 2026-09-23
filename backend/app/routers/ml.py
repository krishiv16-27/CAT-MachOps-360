from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.database import get_db
from ..core.dependencies import get_current_user
from ..schemas.task import ETAPredictionRequest, ETAPredictionResponse
from ..schemas.common import ApiResponse
from ..services.ml_service import ml_service

router = APIRouter()


@router.post("/predict-eta", response_model=ApiResponse[ETAPredictionResponse])
async def predict_eta(
    body: ETAPredictionRequest,
    _=Depends(get_current_user),
):
    result = ml_service.predict_eta(body.model_dump())
    return ApiResponse(data=ETAPredictionResponse(**result))


@router.post("/anomaly-check")
async def anomaly_check(
    body: dict,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    operator_id = body.get("operator_id")
    if not operator_id:
        raise HTTPException(400, "operator_id required")
    result = await ml_service.check_anomaly(operator_id, db)
    return ApiResponse(data=result)


@router.get("/model-status")
async def model_status(_=Depends(get_current_user)):
    return ApiResponse(data={
        "eta_model": "loaded" if ml_service.eta_model else "mock",
        "anomaly_model": "loaded" if ml_service.anomaly_model else "mock",
    })
