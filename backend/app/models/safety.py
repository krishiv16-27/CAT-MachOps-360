"""Alert, SafetyEvent, ProximityEvent, Incident, PrestartCheck, MachinePermission models."""
from datetime import datetime
from sqlalchemy import String, Float, Boolean, DateTime, Text, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column
from ..core.database import Base
from .base_mixin import TimestampMixin, new_uuid


class Alert(Base, TimestampMixin):
    __tablename__ = "alerts"

    alert_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    site_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    zone_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    machine_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    operator_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    task_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # LOW|MEDIUM|HIGH|CRITICAL
    trigger_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_action: Mapped[str | None] = mapped_column(Text, nullable=True)

    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    acknowledged_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledgement_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ProximityEvent(Base):
    __tablename__ = "proximity_events"

    event_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    machine_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    operator_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    zone_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    person_distance_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    nearest_machine_distance_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    nearby_person_count: Mapped[int] = mapped_column(Integer, default=0)
    nearby_machine_count: Mapped[int] = mapped_column(Integer, default=0)
    restricted_zone_entry: Mapped[bool] = mapped_column(Boolean, default=False)
    alert_id: Mapped[str | None] = mapped_column(String(36), nullable=True)


class Incident(Base, TimestampMixin):
    __tablename__ = "incidents"

    incident_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    site_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    zone_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    machine_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    operator_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    task_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    alert_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    category: Mapped[str] = mapped_column(String(50), nullable=False)
    # PROXIMITY|SEATBELT|SPEED|OVERLOAD|EQUIPMENT_FAILURE|ENVIRONMENT|OTHER
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    trigger_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    evidence: Mapped[list | None] = mapped_column(JSON, nullable=True)  # list of file refs

    status: Mapped[str] = mapped_column(String(20), default="OPEN")  # OPEN|INVESTIGATING|RESOLVED
    assigned_to: Mapped[str | None] = mapped_column(String(36), nullable=True)
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    corrective_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_auto_created: Mapped[bool] = mapped_column(Boolean, default=False)


class PrestartCheck(Base, TimestampMixin):
    __tablename__ = "prestart_checks"

    check_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    machine_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    operator_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    items: Mapped[list] = mapped_column(JSON, nullable=False)
    # [{ item_id, label, passed, required, note, blocked_reason }]
    authorization_status: Mapped[str] = mapped_column(String(20), nullable=False)
    # AUTHORIZED|BLOCKED|REVIEW
    blocked_reasons: Mapped[list | None] = mapped_column(JSON, nullable=True)
    review_reasons: Mapped[list | None] = mapped_column(JSON, nullable=True)
    supervisor_override: Mapped[bool] = mapped_column(Boolean, default=False)
    override_by: Mapped[str | None] = mapped_column(String(36), nullable=True)


class MachinePermission(Base, TimestampMixin):
    __tablename__ = "machine_permissions"

    permission_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    machine_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    operator_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    granted_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")
    # ACTIVE|EXPIRED|REVOKED
    prestart_check_id: Mapped[str | None] = mapped_column(String(36), nullable=True)


class DashcamEvent(Base):
    __tablename__ = "dashcam_events"

    event_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    camera_id: Mapped[str] = mapped_column(String(50), nullable=False)
    machine_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    operator_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    person_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    vehicle_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    obstacle_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    restricted_zone_entry: Mapped[bool] = mapped_column(Boolean, default=False)
    estimated_distance_m: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Attention events — labelled as demo simulation only
    attention_event: Mapped[bool] = mapped_column(Boolean, default=False)
    eye_closure_event: Mapped[bool] = mapped_column(Boolean, default=False)
    yawn_event: Mapped[bool] = mapped_column(Boolean, default=False)

    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    frame_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    raw_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    alert_id: Mapped[str | None] = mapped_column(String(36), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    log_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    request_method: Mapped[str | None] = mapped_column(String(10), nullable=True)
    request_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    detail: Mapped[dict | None] = mapped_column(JSON, nullable=True)
