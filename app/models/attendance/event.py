from sqlalchemy import ForeignKey, Integer, String, DateTime, DECIMAL, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional, List

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.studios.studio import Studio
    from app.models.attendance.attendance import Attendance


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (UniqueConstraint("studio_id", "code", name="uq_events_studio_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    studio_id: Mapped[int] = mapped_column(Integer, ForeignKey("studios.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    studio: Mapped["Studio"] = relationship("Studio", back_populates="events")
    attendance: Mapped[List["Attendance"]] = relationship("Attendance", back_populates="event")
