from sqlalchemy import ForeignKey, Integer, String, DateTime, DECIMAL, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, time
from decimal import Decimal
from typing import TYPE_CHECKING
import enum

from app.core.database import Base

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
    hours: Mapped[time] = mapped_column(DateTime, nullable=False)  # Время посещения
    train_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    paid_by: Mapped[PaidBy] = mapped_column(Enum(PaidBy), nullable=False)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("events.id"), nullable=False)
    studio_id: Mapped[int] = mapped_column(Integer, ForeignKey("studios.id"), nullable=False)

    # Связи
    student: Mapped["Student"] = relationship("Student", back_populates="attendance")
    event: Mapped["Event"] = relationship("Event", back_populates="attendance")
    studio: Mapped["Studio"] = relationship("Studio", back_populates="attendance")