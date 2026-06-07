from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional, TYPE_CHECKING

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.students.student import Student


class Belt(Base):
    __tablename__ = "belts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    color: Mapped[str] = mapped_column(String(255), nullable=False)
    style: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    students: Mapped[List["Student"]] = relationship("Student", back_populates="belt")
