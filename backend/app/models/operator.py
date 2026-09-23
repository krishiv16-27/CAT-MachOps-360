"""Operator, certification, and break models."""
from datetime import datetime, date
from sqlalchemy import String, Integer, Float, Boolean, DateTime, Date, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..core.database import Base
from .base_mixin import TimestampMixin, new_uuid


class Operator(Base, TimestampMixin):
    __tablename__ = "operators"

    operator_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    employee_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    site_id: Mapped[str] = mapped_column(String(36), nullable=True, index=True)
    experience_years: Mapped[int] = mapped_column(Integer, default=0)
    skill_level: Mapped[int] = mapped_column(Integer, default=1)  # 1-5
    certification: Mapped[str | None] = mapped_column(String(100), nullable=True)
    certification_expiry: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Current shift state (updated live)
    shift_status: Mapped[str] = mapped_column(
        String(20), default="OFF_SHIFT"
    )  # ON_SHIFT | OFF_SHIFT | ON_BREAK
    shift_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    shift_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    continuous_operating_minutes: Mapped[float] = mapped_column(Float, default=0.0)

    # Current assignment
    current_machine_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    current_task_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    authorization_status: Mapped[str] = mapped_column(
        String(20), default="PENDING"
    )  # AUTHORIZED | BLOCKED | REVIEW | PENDING

    # Safety score (cached, recomputed by scoring service)
    safety_score: Mapped[float] = mapped_column(Float, default=100.0)

    user: Mapped["User"] = relationship("User", back_populates="operator", lazy="select", foreign_keys="[User.operator_id]", uselist=False)
    certifications: Mapped[list["OperatorCertification"]] = relationship(
        "OperatorCertification", back_populates="operator", lazy="select"
    )
    breaks: Mapped[list["OperatorBreak"]] = relationship(
        "OperatorBreak", back_populates="operator", lazy="select"
    )


class OperatorCertification(Base, TimestampMixin):
    __tablename__ = "operator_certifications"

    cert_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    operator_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("operators.operator_id"), nullable=False, index=True
    )
    cert_type: Mapped[str] = mapped_column(String(100), nullable=False)
    cert_code: Mapped[str] = mapped_column(String(50), nullable=False)
    issued_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False)
    issuing_body: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True)

    operator: Mapped["Operator"] = relationship("Operator", back_populates="certifications")


class OperatorBreak(Base, TimestampMixin):
    __tablename__ = "operator_breaks"

    break_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    operator_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("operators.operator_id"), nullable=False, index=True
    )
    break_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    break_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    break_type: Mapped[str] = mapped_column(String(20), default="SCHEDULED")  # SCHEDULED|RECOMMENDED|EMERGENCY
    duration_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)

    operator: Mapped["Operator"] = relationship("Operator", back_populates="breaks")
