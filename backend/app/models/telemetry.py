"""Telemetry, WearableEvent, EnvironmentalData models."""
from datetime import datetime
from sqlalchemy import String, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from ..core.database import Base
from .base_mixin import new_uuid


class Telemetry(Base):
    __tablename__ = "telemetry"

    telemetry_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    site_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    zone_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    machine_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    operator_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    task_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # Engine
    engine_status: Mapped[str] = mapped_column(String(20), default="RUNNING")
    engine_rpm: Mapped[float | None] = mapped_column(Float, nullable=True)
    engine_temperature_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    oil_pressure_psi: Mapped[float | None] = mapped_column(Float, nullable=True)
    coolant_temperature_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    battery_voltage: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Fuel
    fuel_level_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    fuel_consumption_rate_lph: Mapped[float | None] = mapped_column(Float, nullable=True)
    fuel_used_l: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Hydraulics
    hydraulic_pressure_bar: Mapped[float | None] = mapped_column(Float, nullable=True)
    hydraulic_temperature_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    hydraulic_flow_lpm: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Motion
    machine_speed_kmh: Mapped[float | None] = mapped_column(Float, nullable=True)
    machine_load_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    cycle_count: Mapped[int | None] = mapped_column(nullable=True)
    cycle_time_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    idle_time_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    operating_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    vibration_g: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Faults
    fault_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    maintenance_status: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Operator behaviour
    seatbelt_status: Mapped[str | None] = mapped_column(String(20), nullable=True)  # FASTENED|UNFASTENED
    sudden_acceleration: Mapped[bool] = mapped_column(Boolean, default=False)
    sudden_braking: Mapped[bool] = mapped_column(Boolean, default=False)
    sudden_movement: Mapped[bool] = mapped_column(Boolean, default=False)


class WearableEvent(Base):
    __tablename__ = "wearable_events"

    event_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    operator_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    machine_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # Vitals — operational risk indicators ONLY, not medical diagnoses
    heart_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    heart_rate_delta: Mapped[float | None] = mapped_column(Float, nullable=True)
    activity_level: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0-10
    motion_level: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0-10
    skin_temperature_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    wearable_battery_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    wearable_connected: Mapped[bool] = mapped_column(Boolean, default=True)

    # Risk indicators — NOT medical diagnoses
    attention_risk_indicator: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0-1
    fatigue_risk_indicator: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0-1
    self_reported_status: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Optional simulated breathalyzer (separate sensor, explicitly simulated)
    breathalyzer_status: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # CLEAR|REVIEW|BLOCKED — simulated only


class EnvironmentalData(Base):
    __tablename__ = "environmental_data"

    env_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    site_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    temperature_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    humidity_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    rainfall_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    wind_speed_kmh: Mapped[float | None] = mapped_column(Float, nullable=True)
    visibility_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    weather_condition: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ground_condition: Mapped[str | None] = mapped_column(String(50), nullable=True)
    terrain_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    dust_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
