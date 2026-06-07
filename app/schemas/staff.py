from pydantic import BaseModel, ConfigDict, Field
from typing import Literal, Optional
from datetime import datetime


class StaffCreate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "Создание staff-пользователя"})

    username: str = Field(
        min_length=3, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$", description="Уникальный логин"
    )
    password: str = Field(min_length=6, max_length=128, description="Пароль")
    name: str = Field(min_length=1, max_length=255, description="Отображаемое имя")
    role: Literal["admin", "trainer"] = Field(description="Роль в системе")
    studio_short_names: list[str] = Field(
        default_factory=list,
        description="Студии trainer; для trainer — минимум одна",
    )


class StaffUpdate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "Обновление staff-пользователя"})

    name: Optional[str] = Field(default=None, min_length=1, max_length=255, description="Имя")
    password: Optional[str] = Field(
        default=None, min_length=6, max_length=128, description="Новый пароль"
    )
    is_active: Optional[bool] = Field(default=None, description="Активен ли аккаунт")
    studio_short_names: Optional[list[str]] = Field(
        default=None, description="Новый список студий trainer"
    )


class StaffRead(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "Staff-пользователь"})

    username: str = Field(description="Логин")
    name: str = Field(description="Имя")
    role: str = Field(description="admin или trainer")
    is_active: bool = Field(description="Активен ли аккаунт")
    studio_short_names: list[str] = Field(description="Привязанные студии")
    created_at: datetime = Field(description="Дата создания")

    @classmethod
    def from_staff(cls, staff) -> "StaffRead":
        return cls(
            username=staff.username,
            name=staff.name,
            role=staff.role.value,
            is_active=staff.is_active,
            studio_short_names=[s.short_name for s in staff.studios],
            created_at=staff.created_at,
        )
