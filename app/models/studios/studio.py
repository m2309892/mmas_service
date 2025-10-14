from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import List, TYPE_CHECKING

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.students.student import Student
    from app.models.attendance.event import Event
    from app.models.billing.aboniment import Aboniment
    from app.models.attendance.attendance import Attendance


class Studio(Base):
    __tablename__ = "studios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    short_name: Mapped[str] = mapped_column(String(255), nullable=False)
    students_cnt: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # Связи
    students: Mapped[List["Student"]] = relationship("Student", back_populates="studio")
    events: Mapped[List["Event"]] = relationship("Event", back_populates="studio")
    aboniments: Mapped[List["Aboniment"]] = relationship("Aboniment", back_populates="studio")
    attendance: Mapped[List["Attendance"]] = relationship("Attendance", back_populates="studio")
