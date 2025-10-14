from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, TYPE_CHECKING

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.students.student import Student


class Belt(Base):
    __tablename__ = "belts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    color: Mapped[str] = mapped_column(String(255), nullable=False)

    # Связь со студентами
    students: Mapped[List["Student"]] = relationship("Student", back_populates="belt")
