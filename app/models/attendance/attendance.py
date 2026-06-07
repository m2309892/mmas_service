from sqlalchemy import ForeignKey, Integer, Time, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, time
from decimal import Decimal
from typing import TYPE_CHECKING
import enum

from app.core.database import Base, pg_enum

if TYPE_CHECKING:
    from app.models.students.student import Student
    from app.models.attendance.event import Event
    from app.models.studios.studio import Studio


class PaidBy(str, enum.Enum):
    BALANCE = "balance"
    H_ABONIMENT = "hours_aboniment"
    T_ABONEMENT = "time_abonement"
    UNPAID = "unpaid"
    OTHER = "other"


class Attendance(Base):
    __tablename__ = "attendance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id"), nullable=False)
    hours: Mapped[time] = mapped_column(Time, nullable=False)
    train_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    paid_by: Mapped[PaidBy] = mapped_column(pg_enum(PaidBy, "paidby"), nullable=False)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("events.id"), nullable=False)
    studio_id: Mapped[int] = mapped_column(Integer, ForeignKey("studios.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    student: Mapped["Student"] = relationship("Student", back_populates="attendance")
    event: Mapped["Event"] = relationship("Event", back_populates="attendance")
    studio: Mapped["Studio"] = relationship("Studio", back_populates="attendance")