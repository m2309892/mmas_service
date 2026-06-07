from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Literal
from datetime import datetime, date

from app.models.attendance.attendance import PaidBy


class AttendanceBulkItem(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "Одна отметка посещения"})

    mmas_id: str = Field(min_length=1, max_length=255, description="ID студента")
    studio_short_name: str = Field(min_length=1, max_length=50, description="Код студии")
    train_date: datetime = Field(description="Дата и время тренировки")
    hours: int = Field(ge=1, le=24, description="Длительность тренировки в часах")
    event_code: Optional[str] = Field(
        default=None,
        description="Код занятия; если не указан — самое дешёвое в студии",
    )


class AttendanceBulkRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "Пакетная отметка посещений"})

    items: list[AttendanceBulkItem] = Field(
        min_length=1, description="Список посещений для создания"
    )


class AttendanceRead(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "Посещение"})

    mmas_id: str = Field(description="ID студента")
    studio_short_name: str = Field(description="Код студии")
    event_code: str = Field(description="Код занятия")
    train_date: datetime = Field(description="Дата тренировки")
    hours: str = Field(description="Длительность (HH:MM:SS)")
    paid_by: PaidBy = Field(description="Способ оплаты")
    created_at: datetime = Field(description="Время создания записи")

    @classmethod
    def from_attendance(cls, att) -> "AttendanceRead":
        hours_str = att.hours.strftime("%H:%M:%S") if att.hours else "00:00:00"
        event_code = att.event.code if att.event else ""
        return cls(
            mmas_id=att.student.mmas_id if att.student else "",
            studio_short_name=att.studio.short_name if att.studio else "",
            event_code=event_code,
            train_date=att.train_date,
            hours=hours_str,
            paid_by=att.paid_by,
            created_at=att.created_at,
        )


class PayUnpaidRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "Оплата неоплаченных визитов"})

    method: Literal["auto", "balance", "aboniment"] = Field(
        default="auto",
        description="auto: сначала абонемент, потом баланс",
    )


class AttendanceByDateItem(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "Посещение за дату (кратко)"})

    mmas_id: str = Field(description="ID студента")
    studio_short_name: str = Field(description="Код студии")
    event_code: str = Field(description="Код занятия")
    hours: str = Field(description="Длительность")
    paid_by: PaidBy = Field(description="Способ оплаты")


class AttendanceStatsByDate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "Статистика посещаемости за день"})

    target_date: date = Field(description="Дата")
    studio_short_name: Optional[str] = Field(description="Фильтр по студии")
    total_visits: int = Field(description="Всего визитов")
    total_hours: float = Field(description="Суммарные часы")
    unpaid_count: int = Field(description="Неоплаченных визитов")
    by_paid_by: dict[str, int] = Field(description="Разбивка по способу оплаты")
    items: list[AttendanceRead] = Field(description="Детальный список визитов")


class StudentAttendanceStats(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "Статистика студента за период"})

    mmas_id: str = Field(description="ID студента")
    from_date: date = Field(description="Начало периода")
    to_date: date = Field(description="Конец периода")
    total_visits: int = Field(description="Всего визитов")
    total_hours: float = Field(description="Суммарные часы")
    unpaid_count: int = Field(description="Неоплаченных визитов")
    by_paid_by: dict[str, int] = Field(description="Разбивка по способу оплаты")


class StudioAttendanceStats(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "Статистика студии за период"})

    studio_short_name: str = Field(description="Код студии")
    from_date: date = Field(description="Начало периода")
    to_date: date = Field(description="Конец периода")
    total_visits: int = Field(description="Всего визитов")
    unique_students: int = Field(description="Уникальных студентов")
    total_hours: float = Field(description="Суммарные часы")
    unpaid_count: int = Field(description="Неоплаченных визитов")
    by_paid_by: dict[str, int] = Field(description="Разбивка по способу оплаты")
