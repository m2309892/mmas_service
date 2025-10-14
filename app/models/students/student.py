from sqlalchemy import ForeignKey, Integer, String, DateTime, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.studios.studio import Studio
    from app.models.students.belt import Belt
    from app.models.billing.balance_log import BalanceLog
    from app.models.billing.pay_log import PayLog
    from app.models.billing.aboniment import Aboniment
    from app.models.attendance.attendance import Attendance


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    birth_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    gender: Mapped[str] = mapped_column(String(255), nullable=False)
    balance: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), default=0)
    mmas_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    # Внешние ключи
    studio_id: Mapped[int] = mapped_column(Integer, ForeignKey("studios.id"), nullable=False)
    belt_id: Mapped[int] = mapped_column(Integer, ForeignKey("belts.id"), nullable=False)

    # Временные метки
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # Связи
    studio: Mapped["Studio"] = relationship("Studio", back_populates="students")
    belt: Mapped["Belt"] = relationship("Belt", back_populates="students")
    balance_logs: Mapped[List["BalanceLog"]] = relationship("BalanceLog", back_populates="student")
    pay_logs: Mapped[List["PayLog"]] = relationship("PayLog", back_populates="student")
    aboniments: Mapped[List["Aboniment"]] = relationship("Aboniment", back_populates="student")
    attendance: Mapped[List["Attendance"]] = relationship("Attendance", back_populates="student")
