"""
Shift Narrative Service — generates a plain-English paragraph summarising
an operator's shift. Template-based; no LLM required.
"""
from datetime import datetime, timezone, timedelta
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

logger = logging.getLogger(__name__)


async def generate_shift_narrative(operator_id: str, db: AsyncSession) -> dict:
    """
    Pull today's data for the operator and return a structured narrative.
    Returns:
      { narrative: str, sections: {opening, tasks, safety, machine, close},
        metrics: {...}, generated_at: ISO }
    """
    from ..models.operator import Operator
    from ..models.task import Task
    from ..models.safety import Alert
    from ..models.telemetry import Telemetry

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # ── Operator ──────────────────────────────────────────────────────────────
    op_result = await db.execute(select(Operator).where(Operator.operator_id == operator_id))
    op = op_result.scalar_one_or_none()
    if not op:
        return {"narrative": "Operator not found.", "sections": {}, "metrics": {}, "generated_at": now.isoformat()}

    first_name = op.name.split()[0]

    # ── Tasks today ───────────────────────────────────────────────────────────
    tasks_result = await db.execute(
        select(Task).where(
            Task.operator_id == operator_id,
            Task.actual_start >= today_start,
        )
    )
    tasks = tasks_result.scalars().all()
    completed_tasks = [t for t in tasks if t.status == "COMPLETED"]
    in_progress = [t for t in tasks if t.status == "IN_PROGRESS"]

    # Find best-performing task (lowest actual/estimated ratio)
    best_task = None
    best_ratio = 999
    for t in completed_tasks:
        if t.actual_duration_minutes and t.estimated_duration_minutes and t.estimated_duration_minutes > 0:
            ratio = t.actual_duration_minutes / t.estimated_duration_minutes
            if ratio < best_ratio:
                best_ratio = ratio
                best_task = t

    delayed_tasks = [t for t in completed_tasks if t.status == "DELAYED" or
                     (t.actual_duration_minutes and t.estimated_duration_minutes and
                      t.actual_duration_minutes > t.estimated_duration_minutes * 1.20)]

    # ── Alerts today ──────────────────────────────────────────────────────────
    alerts_result = await db.execute(
        select(Alert).where(
            Alert.operator_id == operator_id,
            Alert.timestamp >= today_start,
        )
    )
    alerts = alerts_result.scalars().all()

    # ── Telemetry summary ─────────────────────────────────────────────────────
    telem_result = await db.execute(
        select(Telemetry)
        .where(Telemetry.operator_id == operator_id, Telemetry.timestamp >= today_start)
        .order_by(desc(Telemetry.timestamp))
        .limit(120)
    )
    telemetry = telem_result.scalars().all()

    avg_temp = None
    avg_load = None
    idle_total = 0.0
    anomaly_detected = False
    if telemetry:
        temps = [t.engine_temperature_c for t in telemetry if t.engine_temperature_c]
        loads = [t.machine_load_pct for t in telemetry if t.machine_load_pct]
        idles = [t.idle_time_min for t in telemetry if t.idle_time_min]
        avg_temp = round(sum(temps) / len(temps), 1) if temps else None
        avg_load = round(sum(loads) / len(loads), 1) if loads else None
        idle_total = round(sum(idles), 1) if idles else 0

    # Shift duration
    shift_hours = op.continuous_operating_minutes / 60 if op.continuous_operating_minutes else 8

    # ── Build narrative sections ───────────────────────────────────────────────
    # Opening
    perf_word = "strong" if best_ratio < 0.95 else ("solid" if best_ratio < 1.05 else "steady")
    task_summary = f"{len(completed_tasks)} task{'s' if len(completed_tasks) != 1 else ''} completed"
    if in_progress:
        task_summary += f", 1 in progress"
    opening = (
        f"{first_name}, here's your shift summary. "
        f"You've had a {perf_word} {shift_hours:.0f}-hour shift — {task_summary}."
    )

    # Tasks section
    if best_task:
        pct = round((1 - best_ratio) * 100)
        tasks_section = (
            f"Your best run was a {best_task.task_type.replace('_',' ').title()} task, "
            f"completed {abs(pct)}% {'faster' if pct > 0 else 'slower'} than the estimate."
        )
    elif completed_tasks:
        tasks_section = f"You completed {len(completed_tasks)} tasks on schedule today."
    else:
        tasks_section = "No completed tasks recorded yet for today."
    if delayed_tasks:
        tasks_section += f" Note: {len(delayed_tasks)} task(s) ran over estimate — primarily weather or terrain related."

    # Safety section
    if not alerts:
        safety_section = "No safety alerts during your shift — excellent compliance across the board."
    else:
        alert_types = {}
        for a in alerts:
            alert_types[a.alert_type] = alert_types.get(a.alert_type, 0) + 1
        alert_desc = ", ".join(f"{v}× {k.replace('_',' ').lower()}" for k, v in alert_types.items())
        safety_section = f"Safety events this shift: {alert_desc}."

    # Machine section
    if avg_temp and avg_temp > 100:
        machine_section = (
            f"Your machine ran warmer than usual today — average engine temp {avg_temp}°C. "
            "A coolant check before tomorrow's shift would be worthwhile."
        )
    elif avg_load and avg_load > 75:
        machine_section = f"High average load today ({avg_load:.0f}%) — machine performed well under demanding conditions."
    elif idle_total > 20:
        machine_section = (
            f"The machine logged {idle_total:.0f} minutes of idle time today. "
            "Reducing idle time can save fuel and reduce wear."
        )
    else:
        machine_section = "Machine operated within normal parameters throughout the shift."

    # Close
    if best_task and best_ratio < 0.95:
        close = f"Tomorrow, focus on replicating that efficient {best_task.task_type.replace('_',' ').title()} rhythm — you were in top form."
    elif alerts and any(a.severity in ("HIGH", "CRITICAL") for a in alerts):
        close = "Tomorrow, stay alert for proximity hazards, especially during early morning site activity."
    elif idle_total > 15:
        close = "Tomorrow, aim to cut idle time by keeping planned stops brief — every litre saved counts."
    else:
        close = f"Keep up the consistent work, {first_name}. See you tomorrow."

    # Full narrative
    narrative = " ".join([opening, tasks_section, safety_section, machine_section, close])

    metrics = {
        "tasks_completed": len(completed_tasks),
        "tasks_in_progress": len(in_progress),
        "alerts_count": len(alerts),
        "shift_hours": round(shift_hours, 1),
        "avg_engine_temp_c": avg_temp,
        "avg_load_pct": avg_load,
        "idle_time_min": idle_total,
        "best_task_efficiency_pct": round((1 - best_ratio) * 100, 1) if best_task else None,
    }

    return {
        "narrative": narrative,
        "sections": {
            "opening": opening,
            "tasks": tasks_section,
            "safety": safety_section,
            "machine": machine_section,
            "close": close,
        },
        "metrics": metrics,
        "operator_name": op.name,
        "generated_at": now.isoformat(),
    }
