from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone, date
from ..core.database import get_db
from ..core.dependencies import get_current_user
from ..models.safety import PrestartCheck, MachinePermission
from ..models.operator import Operator, OperatorCertification
from ..models.machine import Machine, MachineFault
from ..schemas.alert import PrestartSubmitRequest, PrestartResponse
from ..schemas.common import ApiResponse
from ..core.ws_manager import ws_manager

router = APIRouter()

CHECKLIST_ITEMS = [
    {"item_id": "auth",        "label": "Operator authenticated",              "required": True},
    {"item_id": "authorized",  "label": "Operator authorized for machine type","required": True},
    {"item_id": "cert_valid",  "label": "Certification valid and not expired", "required": True},
    {"item_id": "seatbelt",    "label": "Seatbelt functional (self-reported)", "required": True},
    {"item_id": "fuel",        "label": "Fuel level ≥ 20%",                   "required": True},
    {"item_id": "health",      "label": "Machine health check passed",         "required": True},
    {"item_id": "no_faults",   "label": "No critical active faults",          "required": True},
    {"item_id": "zone_clear",  "label": "Safety zone clear",                  "required": True},
    {"item_id": "emergency",   "label": "Emergency stop system available",    "required": True},
    {"item_id": "training",    "label": "Required training completed",        "required": True},
    {"item_id": "wearable",    "label": "Wearable device connected",          "required": False},
]


@router.get("/checklist")
async def get_checklist(
    machine_id: str = Query(...),
    operator_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """
    Returns checklist items pre-populated with current system state.
    Frontend displays these to the operator for confirmation.
    """
    items = []
    blocked_reasons = []
    review_reasons = []

    # Fetch operator and machine
    op_result = await db.execute(select(Operator).where(Operator.operator_id == operator_id))
    op = op_result.scalar_one_or_none()

    machine_result = await db.execute(select(Machine).where(Machine.machine_id == machine_id))
    machine = machine_result.scalar_one_or_none()

    for template in CHECKLIST_ITEMS:
        item = {**template, "passed": True, "blocked_reason": None, "auto_checked": False}

        if template["item_id"] == "auth":
            item["auto_checked"] = True  # already authenticated to reach this endpoint

        elif template["item_id"] == "cert_valid" and op:
            if op.certification_expiry and op.certification_expiry < date.today():
                item["passed"] = False
                item["blocked_reason"] = f"EXPIRED: {op.certification_expiry}"
                blocked_reasons.append(f"Certification expired on {op.certification_expiry}")

        elif template["item_id"] == "fuel" and machine and machine.last_fuel_level_pct is not None:
            item["auto_checked"] = True
            if machine.last_fuel_level_pct < 20:
                item["passed"] = False
                item["blocked_reason"] = f"Fuel at {machine.last_fuel_level_pct:.0f}% (minimum 20%)"
                blocked_reasons.append(f"Fuel level too low: {machine.last_fuel_level_pct:.0f}%")

        elif template["item_id"] == "no_faults" and machine:
            faults_result = await db.execute(
                select(MachineFault).where(
                    MachineFault.machine_id == machine_id,
                    MachineFault.is_active == True,
                    MachineFault.severity == "CRITICAL",
                )
            )
            critical_faults = faults_result.scalars().all()
            if critical_faults:
                item["passed"] = False
                item["blocked_reason"] = f"Active critical fault: {critical_faults[0].fault_code}"
                blocked_reasons.append(f"Critical fault: {critical_faults[0].fault_code}")
            item["auto_checked"] = True

        elif template["item_id"] == "health" and machine:
            if machine.last_health_score is not None and machine.last_health_score < 50:
                item["passed"] = False
                item["blocked_reason"] = f"Health score critical: {machine.last_health_score:.0f}%"
                blocked_reasons.append(f"Machine health score critical: {machine.last_health_score:.0f}%")
            item["auto_checked"] = True

        items.append(item)

    if blocked_reasons:
        auth_status = "BLOCKED"
    elif review_reasons:
        auth_status = "REVIEW"
    else:
        auth_status = "AUTHORIZED"

    return ApiResponse(data={
        "machine_id": machine_id,
        "operator_id": operator_id,
        "items": items,
        "preliminary_status": auth_status,
        "blocked_reasons": blocked_reasons,
        "review_reasons": review_reasons,
    })


@router.post("/submit", response_model=ApiResponse[PrestartResponse])
async def submit_checklist(
    body: PrestartSubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    blocked_reasons = []
    review_reasons = []
    required_item_ids = {i["item_id"] for i in CHECKLIST_ITEMS if i["required"]}

    for item in body.items:
        if item.item_id in required_item_ids and not item.passed:
            blocked_reasons.append(f"Required item failed: {item.item_id}")
        elif not item.passed:
            review_reasons.append(f"Optional item not confirmed: {item.item_id}")

    if blocked_reasons:
        auth_status = "BLOCKED"
    elif review_reasons:
        auth_status = "REVIEW"
    else:
        auth_status = "AUTHORIZED"

    check = PrestartCheck(
        machine_id=body.machine_id,
        operator_id=body.operator_id,
        performed_at=datetime.now(timezone.utc),
        items=[i.model_dump() for i in body.items],
        authorization_status=auth_status,
        blocked_reasons=blocked_reasons,
        review_reasons=review_reasons,
    )
    db.add(check)
    await db.flush()

    # Update machine permission record
    if auth_status == "AUTHORIZED":
        perm = MachinePermission(
            machine_id=body.machine_id,
            operator_id=body.operator_id,
            granted_at=datetime.now(timezone.utc),
            granted_by=current_user.user_id,
            status="ACTIVE",
            prestart_check_id=check.check_id,
        )
        db.add(perm)
        # Update machine authorization status
        machine_result = await db.execute(select(Machine).where(Machine.machine_id == body.machine_id))
        machine = machine_result.scalar_one_or_none()
        if machine:
            machine.authorization_status = "AUTHORIZED"

    return ApiResponse(data=PrestartResponse(
        check_id=check.check_id,
        authorization_status=auth_status,
        blocked_reasons=blocked_reasons,
        review_reasons=review_reasons,
        items=[i.model_dump() for i in body.items],
        performed_at=check.performed_at.isoformat(),
    ))
