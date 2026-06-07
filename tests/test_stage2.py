from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import InsufficientBalanceError, AppError
from app.models.billing.balance_log import OperationType
from app.schemas.balance import BalanceLogRead
from app.services.billing.balance_service import credit, debit, refund


def _mock_db_with_student(balance: Decimal):
    student = MagicMock()
    student.id = 1
    student.balance = balance

    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = student
    db.execute = AsyncMock(return_value=result)
    return db, student


@pytest.mark.asyncio
async def test_credit_increases_balance():
    db, student = _mock_db_with_student(Decimal("100"))

    await credit(
        db,
        student_id=1,
        amount=Decimal("50"),
        comment="Пополнение",
        commit=True,
    )

    assert student.balance == Decimal("150")
    db.add.assert_called_once()
    log = db.add.call_args[0][0]
    assert log.operation_type == OperationType.CREDIT
    assert log.amount == Decimal("50")


@pytest.mark.asyncio
async def test_debit_decreases_balance():
    db, student = _mock_db_with_student(Decimal("100"))

    await debit(
        db,
        student_id=1,
        amount=Decimal("30"),
        comment="Списание",
        commit=True,
    )

    assert student.balance == Decimal("70")
    log = db.add.call_args[0][0]
    assert log.operation_type == OperationType.DEBIT


@pytest.mark.asyncio
async def test_debit_insufficient_balance():
    db, student = _mock_db_with_student(Decimal("10"))

    with pytest.raises(InsufficientBalanceError):
        await debit(
            db,
            student_id=1,
            amount=Decimal("50"),
            comment="Списание",
            commit=True,
        )

    assert student.balance == Decimal("10")


@pytest.mark.asyncio
async def test_refund_increases_balance():
    db, student = _mock_db_with_student(Decimal("100"))

    await refund(
        db,
        student_id=1,
        amount=Decimal("25"),
        comment="Возврат",
        commit=True,
    )

    assert student.balance == Decimal("125")
    log = db.add.call_args[0][0]
    assert log.operation_type == OperationType.REFUND


@pytest.mark.asyncio
async def test_zero_amount_rejected():
    db, _ = _mock_db_with_student(Decimal("100"))

    with pytest.raises(AppError):
        await credit(db, student_id=1, amount=Decimal("0"), commit=True)


def test_balance_log_read_source_attendance():
    log = MagicMock()
    log.operation_type = OperationType.DEBIT
    log.amount = Decimal("500")
    log.comment = "test"
    log.created_at = MagicMock()
    log.attendance_id = 42
    log.aboniment_id = None
    log.pay_log_id = None

    read = BalanceLogRead.from_log(log, "MSK-0001")
    assert read.source == "attendance"
    assert read.mmas_id == "MSK-0001"


def test_balance_log_read_source_manual():
    log = MagicMock()
    log.operation_type = OperationType.CREDIT
    log.amount = Decimal("100")
    log.comment = "manual"
    log.created_at = MagicMock()
    log.attendance_id = None
    log.aboniment_id = None
    log.pay_log_id = None

    read = BalanceLogRead.from_log(log, "MSK-0001")
    assert read.source == "manual"
