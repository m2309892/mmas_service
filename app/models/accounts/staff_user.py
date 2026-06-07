import enum
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Integer, String, DateTime, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, pg_enum

if TYPE_CHECKING:
    from app.models.studios.studio import Studio


class StaffRole(str, enum.Enum):
    ADMIN = "admin"
    TRAINER = "trainer"


staff_user_studios = Table(
    "staff_user_studios",
    Base.metadata,
    Column("staff_user_id", Integer, ForeignKey("staff_users.id"), primary_key=True),
    Column("studio_id", Integer, ForeignKey("studios.id"), primary_key=True),
)


class StaffUser(Base):
    __tablename__ = "staff_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[StaffRole] = mapped_column(pg_enum(StaffRole, "staffrole"), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    studios: Mapped[List["Studio"]] = relationship(
        "Studio",
        secondary=staff_user_studios,
        back_populates="staff_users",
    )
