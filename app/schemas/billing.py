from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import date
from decimal import Decimal


class AbonimentCreate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "Выдача абонемента staff"})

    studio_short_name: str = Field(min_length=1, max_length=50, description="Код студии")
    end_date: date = Field(description="Дата окончания действия")
    hours: Optional[int] = Field(
        default=None,
        gt=0,
        description="Оставшиеся часы; не указывать = безлимит по времени",
    )


class AbonimentPurchase(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "Покупка абонемента с баланса"})

    studio_short_name: str = Field(min_length=1, max_length=50, description="Код студии")
    end_date: date = Field(description="Дата окончания")
    hours: Optional[int] = Field(default=None, gt=0, description="Часы абонемента")
    price: Decimal = Field(gt=0, decimal_places=2, description="Сумма списания с баланса")
    comment: Optional[str] = Field(default=None, max_length=500, description="Комментарий")


class AbonimentRead(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "Абонемент студента"})

    mmas_id: str = Field(description="ID студента")
    studio_short_name: str = Field(description="Код студии")
    hours: Optional[int] = Field(description="Оставшиеся часы (null = безлимит по часам)")
    end_date: Optional[date] = Field(description="Дата окончания")
    is_unlimited: bool = Field(description="Безлимит по часам")
    is_active: bool = Field(description="Действует на текущую дату")

    @classmethod
    def from_aboniment(cls, aboniment, *, mmas_id: str) -> "AbonimentRead":
        is_active = (
            aboniment.end_date is not None and aboniment.end_date >= date.today()
        )
        return cls(
            mmas_id=mmas_id,
            studio_short_name=aboniment.studio.short_name,
            hours=aboniment.hours,
            end_date=aboniment.end_date,
            is_unlimited=aboniment.hours is None,
            is_active=is_active,
        )
