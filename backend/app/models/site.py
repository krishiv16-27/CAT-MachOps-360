"""Site and Zone models."""
from sqlalchemy import String, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..core.database import Base
from .base_mixin import TimestampMixin, new_uuid


class Site(Base, TimestampMixin):
    __tablename__ = "sites"

    site_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    site_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    zones: Mapped[list["Zone"]] = relationship("Zone", back_populates="site", lazy="select")


class Zone(Base, TimestampMixin):
    __tablename__ = "zones"

    zone_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    site_id: Mapped[str] = mapped_column(String(36), ForeignKey("sites.site_id"), nullable=False, index=True)
    zone_code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    zone_type: Mapped[str] = mapped_column(String(50), nullable=False, default="WORK")
    speed_limit_kmh: Mapped[float] = mapped_column(Float, default=20.0)
    is_restricted: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    site: Mapped["Site"] = relationship("Site", back_populates="zones", lazy="select")
