from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class EventCreate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "Создание типа занятия"})

    studio_short_name: str = Field(min_length=1, max_length=50, description="Код студии")
    code: str = Field(
        min_length=1,
        max_length=50,
        pattern=r"^[a-z0-9_-]+$",
        description="Публичный код занятия в студии, напр. bjj-group",
    )
    type: str = Field(min_length=1, max_length=50, description="Тип: group, personal и т.д.")
    price: Decimal = Field(gt=0, description="Цена за одно посещение")
    description: Optional[str] = Field(
        default=None, max_length=500, description="Описание занятия"
    )


class EventUpdate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "Обновление занятия"})

    type: Optional[str] = Field(
        default=None, min_length=1, max_length=50, description="Тип занятия"
    )
    price: Optional[Decimal] = Field(default=None, gt=0, description="Цена")
    description: Optional[str] = Field(
        default=None, max_length=500, description="Описание"
    )


class EventRead(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "Тип занятия"})

    studio_short_name: str = Field(description="Код студии")
    code: str = Field(description="Код занятия")
    type: str = Field(description="Тип занятия")
    price: Decimal = Field(description="Цена")
    description: Optional[str] = Field(description="Описание")
    created_at: datetime = Field(description="Дата создания")

    @classmethod
    def from_event(cls, event) -> "EventRead":
        return cls(
            studio_short_name=event.studio.short_name,
            code=event.code,
            type=event.type,
            price=event.price,
            description=event.description,
            created_at=event.created_at,
        )
