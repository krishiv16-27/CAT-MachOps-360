"""Training module, operator training, and recommendations."""
from datetime import datetime, date
from sqlalchemy import String, Float, Boolean, DateTime, Date, Text, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from ..core.database import Base
from .base_mixin import TimestampMixin, new_uuid


class TrainingModule(Base, TimestampMixin):
    __tablename__ = "training_modules"

    module_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    # SAFETY|MACHINE_OPERATION|CERTIFICATION|ENVIRONMENT|EMERGENCY
    module_type: Mapped[str] = mapped_column(String(20), default="VIDEO")
    # VIDEO|SIMULATION|QUIZ|INSTRUCTOR
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=False)
    machine_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class OperatorTraining(Base, TimestampMixin):
    __tablename__ = "operator_training"

    record_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    operator_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    module_id: Mapped[str] = mapped_column(String(36), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="NOT_STARTED")
    # NOT_STARTED|IN_PROGRESS|COMPLETED|EXPIRED
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    assigned_by: Mapped[str | None] = mapped_column(String(36), nullable=True)


class TrainingRecommendation(Base, TimestampMixin):
    __tablename__ = "training_recommendations"

    rec_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    operator_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    module_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # PROXIMITY_EVENTS|EXCESSIVE_IDLE|SPEED_VIOLATIONS|CERT_EXPIRING|ANOMALY
    priority: Mapped[str] = mapped_column(String(20), default="MEDIUM")
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
