"""Operator-related business logic — timeline, shift summary."""
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from ..models.task import Task
from ..models.operator import OperatorBreak
from ..models.safety import Alert
from ..schemas.operator import OperatorTimelineResponse, TimelineEntry
import logging

logger = logging.getLogger(__name__)


async def get_operator_timeline(operator_id: str, date_str: str | None, db: AsyncSession) -> OperatorTimelineResponse:
    if date_str:
        target_date = datetime.fromisoformat(date_str).date()
    else:
        target_date = datetime.now(timezone.utc).date()

    day_start = datetime(target_date.year, target_date.month, target_date.day, tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)

    # Fetch tasks for the day
    tasks_result = await db.execute(
        select(Task).where(
            Task.operator_id == operator_id,
            Task.actual_start >= day_start,
            Task.actual_start < day_end,
        )
    )
    tasks = tasks_result.scalars().all()

    # Fetch breaks for the day
    breaks_result = await db.execute(
        select(OperatorBreak).where(
            OperatorBreak.operator_id == operator_id,
            OperatorBreak.break_start >= day_start,
            OperatorBreak.break_start < day_end,
        )
    )
    breaks = breaks_result.scalars().all()

    # Fetch safety events for the day
    alerts_result = await db.execute(
        select(Alert).where(
            Alert.operator_id == operator_id,
            Alert.timestamp >= day_start,
            Alert.timestamp < day_end,
        )
    )
    alerts = alerts_result.scalars().all()

    entries: list[TimelineEntry] = []

    for task in sorted(tasks, key=lambda t: t.actual_start or day_start):
        duration = None
        if task.actual_start and task.actual_end:
            duration = (task.actual_end - task.actual_start).total_seconds() / 60
        entries.append(TimelineEntry(
            entry_type="TASK",
            start_time=task.actual_start or day_start,
            end_time=task.actual_end,
            duration_minutes=duration or task.actual_duration_minutes,
            label=task.task_type,
            machine_id=task.machine_id,
            zone_id=task.zone_id,
            status=task.status,
            metadata={
                "task_id": task.task_id,
                "estimated_duration_minutes": task.estimated_duration_minutes,
                "predicted_duration_minutes": task.predicted_duration_minutes,
                "completed_quantity": task.completed_quantity,
                "target_quantity": task.target_quantity,
                "unit": task.unit,
            },
        ))

    for brk in breaks:
        duration = brk.duration_minutes
        if not duration and brk.break_end:
            duration = (brk.break_end - brk.break_start).total_seconds() / 60
        entries.append(TimelineEntry(
            entry_type="BREAK",
            start_time=brk.break_start,
            end_time=brk.break_end,
            duration_minutes=duration,
            label=f"{brk.break_type} Break",
            machine_id=None,
            zone_id=None,
            status=None,
        ))

    for alert in alerts:
        entries.append(TimelineEntry(
            entry_type="SAFETY_EVENT",
            start_time=alert.timestamp,
            end_time=None,
            duration_minutes=None,
            label=alert.alert_type.replace("_", " "),
            machine_id=alert.machine_id,
            zone_id=alert.zone_id,
            status=alert.severity,
            metadata={"alert_id": alert.alert_id, "message": alert.message},
        ))

    entries.sort(key=lambda e: e.start_time)

    # Totals
    total_operating = sum(e.duration_minutes or 0 for e in entries if e.entry_type == "TASK")
    total_break = sum(e.duration_minutes or 0 for e in entries if e.entry_type == "BREAK")
    safety_event_count = sum(1 for e in entries if e.entry_type == "SAFETY_EVENT")

    return OperatorTimelineResponse(
        operator_id=operator_id,
        date=target_date.isoformat(),
        entries=entries,
        totals={
            "operating_minutes": round(total_operating, 1),
            "break_minutes": round(total_break, 1),
            "tasks_completed": sum(1 for t in tasks if t.status == "COMPLETED"),
            "tasks_total": len(tasks),
            "safety_events": safety_event_count,
        },
    )
