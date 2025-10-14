from sqlalchemy import ForeignKey, Integer, String, DateTime, DECIMAL, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
import enum

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.students.student import Student

    
class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class PayLog(Base):
    __tablename__ = "pay_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    yookassa_id: Mapped[str] = mapped_column(String(255), nullable=False)
    student_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("students.id"), nullable=True)
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), nullable=False)
    user_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # Связи
    student: Mapped[Optional["Student"]] = relationship("Student", back_populates="pay_logs")
