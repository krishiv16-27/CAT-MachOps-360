"""User model — authentication and RBAC."""
from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..core.database import Base
from .base_mixin import TimestampMixin, new_uuid


class User(Base, TimestampMixin):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(50), nullable=False, default="operator"
    )  # operator|supervisor|engineer|safety_officer|maintenance_engineer|admin
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    operator_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("operators.operator_id"), nullable=True
    )

    operator: Mapped["Operator"] = relationship("Operator", back_populates="user", lazy="select", foreign_keys="[User.operator_id]")

    def __repr__(self):
        return f"<User {self.email} role={self.role}>"
