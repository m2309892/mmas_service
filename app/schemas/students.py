from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class StudentCreate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "Регистрация студента"})

    name: str = Field(min_length=1, max_length=255, description="ФИО")
    password: str = Field(min_length=6, max_length=128, description="Пароль для входа")
    birth_date: datetime = Field(description="Дата рождения")
    gender: str = Field(min_length=1, max_length=255, description="Пол")
    studio_short_name: str = Field(min_length=1, max_length=50, description="Код студии")
    belt_code: str = Field(min_length=1, max_length=50, description="Код пояса")


class StudentUpdate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "Обновление профиля студента"})

    name: str | None = Field(default=None, min_length=1, max_length=255, description="ФИО")
    password: str | None = Field(
        default=None, min_length=6, max_length=128, description="Новый пароль"
    )
    birth_date: datetime | None = Field(default=None, description="Дата рождения")
    gender: str | None = Field(default=None, min_length=1, max_length=255, description="Пол")
    belt_code: str | None = Field(default=None, min_length=1, max_length=50, description="Код пояса")


class StudentRead(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "Карточка студента"})

    mmas_id: str = Field(description="Публичный ID")
    name: str = Field(description="ФИО")
    birth_date: datetime = Field(description="Дата рождения")
    gender: str = Field(description="Пол")
    balance: Decimal = Field(description="Баланс в рублях")
    studio_short_name: str = Field(description="Код студии")
    belt_code: str = Field(description="Код пояса")
    belt_color: str = Field(description="Цвет пояса")
    created_at: datetime = Field(description="Дата регистрации")
    updated_at: datetime = Field(description="Дата обновления")

    @classmethod
    def from_student(cls, student) -> "StudentRead":
        return cls(
            mmas_id=student.mmas_id,
            name=student.name,
            birth_date=student.birth_date,
            gender=student.gender,
            balance=student.balance,
            studio_short_name=student.studio.short_name,
            belt_code=student.belt.code,
            belt_color=student.belt.color,
            created_at=student.created_at,
            updated_at=student.updated_at,
        )


class StudentProjection(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "Краткая проекция студента"})

    mmas_id: str = Field(description="Публичный ID")
    name: str = Field(description="ФИО")
    belt_color: str = Field(description="Цвет пояса")

    @classmethod
    def from_row(cls, row: tuple) -> "StudentProjection":
        return cls(mmas_id=row[0], name=row[1], belt_color=row[2])


class BalanceByTgItem(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "Баланс привязанного студента"})

    mmas_id: str = Field(description="ID студента")
    balance: int = Field(description="Баланс в рублях")


class BalanceResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "Текущий баланс студента"})

    mmas_id: str = Field(description="ID студента")
    balance: Optional[int] = Field(description="Баланс в рублях")
