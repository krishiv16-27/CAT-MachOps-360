"""
Additional operator models: NearMissEvent, GutCheckResponse.
Added in Phase C to support unique operator-first features.
"""
from datetime import datetime
from sqlalchemy import String, Float, Boolean, DateTime, Integer, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from ..core.database import Base
from .base_mixin import new_uuid


class NearMissEvent(Base):
    """
    Self-corrected near-miss events detected by the safety engine.
    Recorded when an operator reacts to a proximity hazard BEFORE an alert fires.
    """
    __tablename__ = "near_miss_events"

    event_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    operator_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    machine_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    person_distance_m: Mapped[float] = mapped_column(Float, nullable=False)
    operator_response_time_sec: Mapped[float] = mapped_column(Float, nullable=False)
    was_self_corrected: Mapped[bool] = mapped_column(Boolean, default=True)
    # Severity this would have been if the operator hadn't reacted
    alert_would_have_been: Mapped[str] = mapped_column(String(20), default="MEDIUM")
    speed_before_kmh: Mapped[float | None] = mapped_column(Float, nullable=True)
    speed_after_kmh: Mapped[float | None] = mapped_column(Float, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class GutCheckResponse(Base):
    """
    Pre-shift gut check responses. Voluntary wellness indicators only.
    NOT medical data — used solely for supervisor awareness.
    """
    __tablename__ = "gut_check_responses"

    response_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    operator_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # Three voluntary yes/no questions
    ready_for_shift: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    feeling_well: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    slept_enough: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    # 0–100% readiness score (count of "yes" / 3 * 100)
    readiness_score: Mapped[int] = mapped_column(Integer, default=100)
    # If score < 67%, supervisor notification was sent
    supervisor_notified: Mapped[bool] = mapped_column(Boolean, default=False)
    shift_date: Mapped[str] = mapped_column(String(10), nullable=False)  # YYYY-MM-DD
