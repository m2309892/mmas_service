from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Literal
from datetime import datetime
from decimal import Decimal

from app.models.billing.balance_log import OperationType


class BalanceAdjustRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "Операция с балансом"})

    amount: Decimal = Field(gt=0, decimal_places=2, description="Сумма в рублях")
    comment: str = Field(min_length=1, max_length=500, description="Комментарий к операции")


class BalanceLogRead(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "Запись журнала баланса"})

    operation_type: OperationType = Field(description="credit, debit или refund")
    mmas_id: str = Field(description="ID студента")
    amount: Decimal = Field(description="Сумма операции")
    comment: Optional[str] = Field(description="Комментарий")
    source: Literal["attendance", "aboniment", "payment", "manual"] = Field(
        description="Источник: посещение, абонемент, платёж или ручная операция"
    )
    created_at: datetime = Field(description="Время операции")

    @classmethod
    def from_log(cls, log, mmas_id: str) -> "BalanceLogRead":
        if log.attendance_id:
            source = "attendance"
        elif log.aboniment_id:
            source = "aboniment"
        elif log.pay_log_id:
            source = "payment"
        else:
            source = "manual"

        return cls(
            operation_type=log.operation_type,
            mmas_id=mmas_id,
            amount=log.amount,
            comment=log.comment,
            source=source,
            created_at=log.created_at,
        )
