"""Machine, MachineModel, MachineFault, and Maintenance models."""
from datetime import datetime, date
from sqlalchemy import String, Integer, Float, Boolean, DateTime, Date, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..core.database import Base
from .base_mixin import TimestampMixin, new_uuid


class MachineModel(Base, TimestampMixin):
    __tablename__ = "machine_models"

    model_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    manufacturer: Mapped[str] = mapped_column(String(100), default="Caterpillar")
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    machine_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # EXCAVATOR|BULLDOZER|GRADER|LOADER|DUMP_TRUCK|COMPACTOR|SCRAPER
    nominal_rpm_min: Mapped[float] = mapped_column(Float, default=800.0)
    nominal_rpm_max: Mapped[float] = mapped_column(Float, default=2200.0)
    nominal_hydraulic_pressure_bar: Mapped[float] = mapped_column(Float, default=250.0)
    fuel_tank_capacity_l: Mapped[float] = mapped_column(Float, default=500.0)
    max_load_tons: Mapped[float] = mapped_column(Float, default=30.0)
    service_interval_hours: Mapped[int] = mapped_column(Integer, default=500)

    machines: Mapped[list["Machine"]] = relationship("Machine", back_populates="model", lazy="select")


class Machine(Base, TimestampMixin):
    __tablename__ = "machines"

    machine_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    machine_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    model_id: Mapped[str] = mapped_column(String(36), ForeignKey("machine_models.model_id"), nullable=False, index=True)
    site_id: Mapped[str] = mapped_column(String(36), nullable=True, index=True)
    zone_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    year_manufactured: Mapped[int] = mapped_column(Integer, nullable=False)
    engine_hours: Mapped[float] = mapped_column(Float, default=0.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Current state
    status: Mapped[str] = mapped_column(
        String(20), default="INACTIVE"
    )  # ACTIVE|INACTIVE|MAINTENANCE|FAULT
    current_operator_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    current_task_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    authorization_status: Mapped[str] = mapped_column(String(20), default="PENDING")

    # Latest telemetry snapshot (cached for fast dashboard reads)
    last_engine_rpm: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_engine_temp_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_fuel_level_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_machine_load_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_speed_kmh: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_health_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    model: Mapped["MachineModel"] = relationship("MachineModel", back_populates="machines", lazy="joined")
    faults: Mapped[list["MachineFault"]] = relationship(
        "MachineFault", back_populates="machine", lazy="select"
    )
    maintenance_records: Mapped[list["MachineMaintenance"]] = relationship(
        "MachineMaintenance", back_populates="machine", lazy="select"
    )


class MachineFault(Base, TimestampMixin):
    __tablename__ = "machine_faults"

    fault_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    machine_id: Mapped[str] = mapped_column(String(36), ForeignKey("machines.machine_id"), nullable=False, index=True)
    fault_code: Mapped[str] = mapped_column(String(20), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="MEDIUM")
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    machine: Mapped["Machine"] = relationship("Machine", back_populates="faults")


class MachineMaintenance(Base, TimestampMixin):
    __tablename__ = "machine_maintenance"

    maintenance_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    machine_id: Mapped[str] = mapped_column(String(36), ForeignKey("machines.machine_id"), nullable=False, index=True)
    maintenance_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # OIL_CHANGE|FILTER|HYDRAULIC_SERVICE|FULL_SERVICE|INSPECTION
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    engine_hours_at_service: Mapped[float] = mapped_column(Float, nullable=False)
    performed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_service_hours: Mapped[float | None] = mapped_column(Float, nullable=True)

    machine: Mapped["Machine"] = relationship("Machine", back_populates="maintenance_records")
