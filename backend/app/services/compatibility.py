"""
Operator-Machine Compatibility Score Service.
Score 0–100 based on 5 weighted components.
"""
from datetime import datetime, timezone
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

logger = logging.getLogger(__name__)

WEIGHTS = {
    "experience_match": 0.20,
    "machine_familiarity": 0.25,
    "task_match": 0.20,
    "condition_match": 0.20,
    "machine_condition": 0.15,
}


async def get_compatibility_score(
    operator_id: str,
    machine_id: str,
    task_type: str | None,
    db: AsyncSession,
) -> dict:
    from ..models.operator import Operator
    from ..models.machine import Machine
    from ..models.task import Task

    op_result = await db.execute(select(Operator).where(Operator.operator_id == operator_id))
    op = op_result.scalar_one_or_none()

    mach_result = await db.execute(select(Machine).where(Machine.machine_id == machine_id))
    mach = mach_result.scalar_one_or_none()

    if not op or not mach:
        return {"score": 0, "label": "UNKNOWN", "components": {}, "recommendation": "Operator or machine not found."}

    # ── Component 1: Experience match ──────────────────────────────────────────
    # Skill level vs machine complexity (proxy: engine_hours / 1000)
    machine_complexity = min(5, max(1, int(mach.engine_hours / 2000) + 1))
    skill_gap = abs(op.skill_level - machine_complexity)
    exp_score = max(0, 100 - skill_gap * 18)

    # ── Component 2: Machine familiarity ──────────────────────────────────────
    # How many completed tasks has this operator done on this specific machine?
    fam_result = await db.execute(
        select(func.count()).select_from(Task).where(
            Task.operator_id == operator_id,
            Task.machine_id == machine_id,
            Task.status == "COMPLETED",
        )
    )
    familiarity_count = fam_result.scalar() or 0
    fam_score = min(100, 40 + familiarity_count * 12)

    # ── Component 3: Task match ────────────────────────────────────────────────
    if task_type:
        task_match_result = await db.execute(
            select(func.count()).select_from(Task).where(
                Task.operator_id == operator_id,
                Task.task_type == task_type.upper(),
                Task.status == "COMPLETED",
            )
        )
        task_count = task_match_result.scalar() or 0
        task_score = min(100, 50 + task_count * 8)
    else:
        task_score = 70  # neutral when no task specified

    # ── Component 4: Condition match ───────────────────────────────────────────
    # Simplified: based on operator experience_years (more experienced = better in all conditions)
    cond_score = min(100, 50 + op.experience_years * 3)

    # ── Component 5: Machine condition ────────────────────────────────────────
    health = mach.last_health_score or 85.0
    mach_score = min(100, health)

    # ── Weighted total ─────────────────────────────────────────────────────────
    total = (
        exp_score   * WEIGHTS["experience_match"]
        + fam_score * WEIGHTS["machine_familiarity"]
        + task_score * WEIGHTS["task_match"]
        + cond_score * WEIGHTS["condition_match"]
        + mach_score * WEIGHTS["machine_condition"]
    )
    total = round(min(100, max(0, total)), 1)

    if total >= 88:
        label = "EXCELLENT"
    elif total >= 70:
        label = "SUITABLE"
    elif total >= 50:
        label = "MARGINAL"
    else:
        label = "NOT_RECOMMENDED"

    # Build recommendation text
    mach_code = mach.machine_code
    first = op.name.split()[0]
    if label == "EXCELLENT":
        rec = (
            f"{first} is an excellent match for {mach_code}. "
            f"{familiarity_count} successful task{'s' if familiarity_count != 1 else ''} on this machine, "
            f"skill level {op.skill_level}/5 aligns well."
        )
    elif label == "SUITABLE":
        rec = (
            f"{first} is a solid match for {mach_code}. "
            f"Minor experience gap in specific conditions — suitable for standard operations."
        )
    elif label == "MARGINAL":
        rec = (
            f"{first} can operate {mach_code} with supervision. "
            f"Additional training on this machine type is recommended."
        )
    else:
        rec = (
            f"Assignment of {first} to {mach_code} is not recommended at this time. "
            f"Skill gap or machine condition requires resolution first."
        )

    if mach.status == "MAINTENANCE":
        rec = f"{mach_code} is currently in maintenance and cannot be assigned."
        label = "UNAVAILABLE"
        total = 0

    return {
        "operator_id": operator_id,
        "machine_id": machine_id,
        "operator_name": op.name,
        "machine_code": mach_code,
        "machine_status": mach.status,
        "task_type": task_type,
        "score": total,
        "label": label,
        "components": {
            "experience_match": {"score": round(exp_score, 1), "weight": WEIGHTS["experience_match"],
                                  "detail": f"Skill L{op.skill_level} vs machine complexity L{machine_complexity}"},
            "machine_familiarity": {"score": round(fam_score, 1), "weight": WEIGHTS["machine_familiarity"],
                                     "detail": f"{familiarity_count} prior tasks on this machine"},
            "task_match": {"score": round(task_score, 1), "weight": WEIGHTS["task_match"],
                            "detail": f"Experience with {task_type or 'various'} tasks"},
            "condition_match": {"score": round(cond_score, 1), "weight": WEIGHTS["condition_match"],
                                 "detail": f"{op.experience_years}yr experience"},
            "machine_condition": {"score": round(mach_score, 1), "weight": WEIGHTS["machine_condition"],
                                   "detail": f"Machine health {health:.0f}%"},
        },
        "recommendation": rec,
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }
