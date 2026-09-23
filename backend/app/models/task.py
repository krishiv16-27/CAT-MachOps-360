"""Task, TaskAssignment, and TaskEvent models."""
from datetime import datetime
from sqlalchemy import String, Float, Boolean, DateTime, Text, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..core.database import Base
from .base_mixin import TimestampMixin, new_uuid


class Task(Base, TimestampMixin):
    __tablename__ = "tasks"

    task_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    site_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    zone_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    machine_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    operator_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # EXCAVATION|LOADING|TRENCHING|GRADING|HAULING|COMPACTION|BACKFILL
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    material_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    target_quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    completed_quantity: Mapped[float] = mapped_column(Float, default=0.0)
    unit: Mapped[str | None] = mapped_column(String(20), nullable=True)  # m3|tons|m

    status: Mapped[str] = mapped_column(
        String(20), default="PENDING"
    )  # PENDING|IN_PROGRESS|COMPLETED|DELAYED|PAUSED|CANCELLED

    scheduled_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    estimated_duration_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_duration_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)
    predicted_duration_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)  # ML output

    # Context at time of task
    weather_condition: Mapped[str | None] = mapped_column(String(50), nullable=True)
    terrain_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    delay_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    priority: Mapped[int] = mapped_column(Integer, default=2)  # 1=HIGH 2=MEDIUM 3=LOW

    events: Mapped[list["TaskEvent"]] = relationship("TaskEvent", back_populates="task", lazy="select")


class TaskEvent(Base, TimestampMixin):
    __tablename__ = "task_events"

    event_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    task_id: Mapped[str] = mapped_column(String(36), ForeignKey("tasks.task_id"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # STARTED|PAUSED|RESUMED|COMPLETED|DELAYED|QUANTITY_UPDATE
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    operator_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    quantity_delta: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    task: Mapped["Task"] = relationship("Task", back_populates="events")
