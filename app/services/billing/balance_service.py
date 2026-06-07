from decimal import Decimal
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, NotFoundError, InsufficientBalanceError
from app.models.students.student import Student
from app.models.billing.balance_log import BalanceLog, OperationType


async def _get_student(db: AsyncSession, student_id: int) -> Student:
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if student is None:
        raise NotFoundError(f"Student with id={student_id} not found")
    return student


async def _apply_operation(
    db: AsyncSession,
    *,
    student_id: int,
    amount: Decimal,
    operation_type: OperationType,
    comment: Optional[str] = None,
    attendance_id: Optional[int] = None,
    aboniment_id: Optional[int] = None,
    pay_log_id: Optional[int] = None,
    allow_negative: bool = False,
    commit: bool = True,
) -> BalanceLog:
    if amount <= 0:
        raise AppError("Amount must be positive")

    student = await _get_student(db, student_id)
    current = Decimal(str(student.balance))

    if operation_type == OperationType.DEBIT:
        if not allow_negative and current < amount:
            raise InsufficientBalanceError(
                f"Insufficient balance: have {current}, need {amount}"
            )
        student.balance = current - amount
    else:
        student.balance = current + amount

    log = BalanceLog(
        operation_type=operation_type,
        student_id=student_id,
        amount=amount,
        comment=comment,
        attendance_id=attendance_id,
        aboniment_id=aboniment_id,
        pay_log_id=pay_log_id,
        created_at=datetime.now(),
    )
    db.add(log)

    if commit:
        await db.commit()
        await db.refresh(log)
        await db.refresh(student)
    else:
        await db.flush()
        await db.refresh(log)

    return log


async def credit(
    db: AsyncSession,
    *,
    student_id: int,
    amount: Decimal,
    comment: Optional[str] = None,
    aboniment_id: Optional[int] = None,
    pay_log_id: Optional[int] = None,
    commit: bool = True,
) -> BalanceLog:
    return await _apply_operation(
        db,
        student_id=student_id,
        amount=amount,
        operation_type=OperationType.CREDIT,
        comment=comment,
        aboniment_id=aboniment_id,
        pay_log_id=pay_log_id,
        commit=commit,
    )


async def debit(
    db: AsyncSession,
    *,
    student_id: int,
    amount: Decimal,
    comment: Optional[str] = None,
    attendance_id: Optional[int] = None,
    aboniment_id: Optional[int] = None,
    allow_negative: bool = False,
    commit: bool = True,
) -> BalanceLog:
    return await _apply_operation(
        db,
        student_id=student_id,
        amount=amount,
        operation_type=OperationType.DEBIT,
        comment=comment,
        attendance_id=attendance_id,
        aboniment_id=aboniment_id,
        allow_negative=allow_negative,
        commit=commit,
    )


async def refund(
    db: AsyncSession,
    *,
    student_id: int,
    amount: Decimal,
    comment: Optional[str] = None,
    pay_log_id: Optional[int] = None,
    commit: bool = True,
) -> BalanceLog:
    return await _apply_operation(
        db,
        student_id=student_id,
        amount=amount,
        operation_type=OperationType.REFUND,
        comment=comment,
        pay_log_id=pay_log_id,
        commit=commit,
    )


async def credit_by_mmas_id(
    db: AsyncSession,
    *,
    mmas_id: str,
    amount: Decimal,
    comment: Optional[str] = None,
    commit: bool = True,
) -> BalanceLog:
    from app.services.students.service import get_student_by_mmas_id

    student = await get_student_by_mmas_id(db, mmas_id)
    return await credit(
        db,
        student_id=student.id,
        amount=amount,
        comment=comment,
        commit=commit,
    )


async def debit_by_mmas_id(
    db: AsyncSession,
    *,
    mmas_id: str,
    amount: Decimal,
    comment: Optional[str] = None,
    allow_negative: bool = False,
    commit: bool = True,
) -> BalanceLog:
    from app.services.students.service import get_student_by_mmas_id

    student = await get_student_by_mmas_id(db, mmas_id)
    return await debit(
        db,
        student_id=student.id,
        amount=amount,
        comment=comment,
        allow_negative=allow_negative,
        commit=commit,
    )


async def refund_by_mmas_id(
    db: AsyncSession,
    *,
    mmas_id: str,
    amount: Decimal,
    comment: Optional[str] = None,
    commit: bool = True,
) -> BalanceLog:
    from app.services.students.service import get_student_by_mmas_id

    student = await get_student_by_mmas_id(db, mmas_id)
    return await refund(
        db,
        student_id=student.id,
        amount=amount,
        comment=comment,
        commit=commit,
    )
