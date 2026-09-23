from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone
from ..core.database import get_db
from ..core.dependencies import get_current_user, require_role, PaginationParams
from ..models.task import Task, TaskEvent
from ..schemas.task import TaskOut, TaskCreate, TaskUpdate
from ..schemas.common import ApiResponse
from ..core.ws_manager import ws_manager

router = APIRouter()


@router.get("", response_model=ApiResponse[list[TaskOut]])
async def list_tasks(
    operator_id: str | None = Query(None),
    machine_id: str | None = Query(None),
    status: str | None = Query(None),
    site_id: str | None = Query(None),
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = select(Task)
    if current_user.role == "operator":
        q = q.where(Task.operator_id == current_user.operator_id)
    else:
        if operator_id:
            q = q.where(Task.operator_id == operator_id)
        if machine_id:
            q = q.where(Task.machine_id == machine_id)
        if site_id:
            q = q.where(Task.site_id == site_id)
    if status:
        q = q.where(Task.status == status.upper())
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar()
    q = q.offset(pagination.offset).limit(pagination.page_size)
    result = await db.execute(q)
    tasks = result.scalars().all()
    return ApiResponse(data=[TaskOut.model_validate(t) for t in tasks], meta={"total": total})


@router.get("/{task_id}", response_model=ApiResponse[TaskOut])
async def get_task(task_id: str, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(Task).where(Task.task_id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(404, "Task not found")
    return ApiResponse(data=TaskOut.model_validate(task))


@router.post("", response_model=ApiResponse[TaskOut])
async def create_task(
    body: TaskCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role(["supervisor", "engineer", "admin"])),
):
    task = Task(**body.model_dump())
    db.add(task)
    await db.flush()
    return ApiResponse(data=TaskOut.model_validate(task))


@router.post("/{task_id}/start")
async def start_task(task_id: str, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(Task).where(Task.task_id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(404, "Task not found")
    task.status = "IN_PROGRESS"
    task.actual_start = datetime.now(timezone.utc)
    event = TaskEvent(
        task_id=task_id,
        event_type="STARTED",
        timestamp=datetime.now(timezone.utc),
        operator_id=task.operator_id,
    )
    db.add(event)
    # Broadcast task update
    await ws_manager.broadcast({
        "type": "TASK_UPDATE",
        "payload": {
            "task_id": task_id,
            "operator_id": task.operator_id,
            "machine_id": task.machine_id,
            "status": "IN_PROGRESS",
            "progress_pct": 0,
        },
    })
    return ApiResponse(data={"task_id": task_id, "status": "IN_PROGRESS"})


@router.post("/{task_id}/complete")
async def complete_task(task_id: str, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(Task).where(Task.task_id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(404, "Task not found")
    task.status = "COMPLETED"
    task.actual_end = datetime.now(timezone.utc)
    if task.actual_start:
        delta = (task.actual_end - task.actual_start).total_seconds() / 60
        task.actual_duration_minutes = delta
    event = TaskEvent(
        task_id=task_id,
        event_type="COMPLETED",
        timestamp=datetime.now(timezone.utc),
        operator_id=task.operator_id,
    )
    db.add(event)
    return ApiResponse(data={"task_id": task_id, "status": "COMPLETED"})


@router.patch("/{task_id}", response_model=ApiResponse[TaskOut])
async def update_task(
    task_id: str,
    body: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(select(Task).where(Task.task_id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(404, "Task not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(task, field, value)
    return ApiResponse(data=TaskOut.model_validate(task))
