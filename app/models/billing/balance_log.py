from sqlalchemy import ForeignKey, Integer, String, DateTime, DECIMAL, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
import enum

from app.core.database import Base


if TYPE_CHECKING:
    from app.models.students.student import Student

class OperationType(str, enum.Enum):
    CREDIT = "credit"  # Пополнение
    DEBIT = "debit"    # Списание


class BalanceLog(Base):
    __tablename__ = "balance_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    operation_type: Mapped[OperationType] = mapped_column(Enum(OperationType), nullable=False)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # Связи
    student: Mapped["Student"] = relationship("Student", back_populates="balance_logs")
