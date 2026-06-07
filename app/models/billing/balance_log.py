from sqlalchemy import ForeignKey, Integer, String, DateTime, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
import enum

from app.core.database import Base, pg_enum


if TYPE_CHECKING:
    from app.models.students.student import Student
    from app.models.attendance.attendance import Attendance
    from app.models.billing.aboniment import Aboniment
    from app.models.billing.pay_log import PayLog


class OperationType(str, enum.Enum):
    CREDIT = "credit"
    DEBIT = "debit"
    REFUND = "refund"


class BalanceLog(Base):
    __tablename__ = "balance_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    operation_type: Mapped[OperationType] = mapped_column(
        pg_enum(OperationType, "operationtype"), nullable=False
    )
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    attendance_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("attendance.id"), nullable=True
    )
    aboniment_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("aboniments.id"), nullable=True
    )
    pay_log_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("pay_logs.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    student: Mapped["Student"] = relationship("Student", back_populates="balance_logs")
    attendance: Mapped[Optional["Attendance"]] = relationship("Attendance")
    aboniment: Mapped[Optional["Aboniment"]] = relationship("Aboniment")
    pay_log: Mapped[Optional["PayLog"]] = relationship("PayLog")
