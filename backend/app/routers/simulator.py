from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.database import get_db
from ..core.dependencies import require_role
from ..services.simulator_service import SimulatorService
from ..schemas.common import ApiResponse

router = APIRouter()
_active_scenario = {"name": None, "activated_at": None, "events_injected": 0}


@router.post("/activate")
async def activate_scenario(
    body: dict,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role(["engineer", "supervisor", "admin"])),
):
    scenario = body.get("scenario", "NORMAL_OPERATION")
    machine_id = body.get("machine_id")
    operator_id = body.get("operator_id")

    svc = SimulatorService(db)
    result = await svc.activate(scenario, machine_id=machine_id, operator_id=operator_id)
    _active_scenario["name"] = scenario
    _active_scenario["activated_at"] = result.get("activated_at")
    _active_scenario["events_injected"] = result.get("events_injected", 0)
    return ApiResponse(data=result)


@router.post("/reset")
async def reset_simulator(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role(["engineer", "supervisor", "admin"])),
):
    svc = SimulatorService(db)
    await svc.reset()
    _active_scenario["name"] = None
    return ApiResponse(data={"status": "reset", "message": "Simulator reset to normal operation"})


@router.get("/status")
async def simulator_status(_=Depends(require_role(["engineer", "supervisor", "admin"]))):
    return ApiResponse(data=_active_scenario)
