from sqlalchemy import ForeignKey, Integer, String, Date, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.students.student import Student
    from app.models.studios.studio import Studio
    
class Aboniment(Base):
    __tablename__ = "aboniments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("students.id"), nullable=True)
    studio_id: Mapped[int] = mapped_column(Integer, ForeignKey("studios.id"), nullable=False)
    hours: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    student: Mapped[Optional["Student"]] = relationship("Student", back_populates="aboniments")
    studio: Mapped["Studio"] = relationship("Studio", back_populates="aboniments")
