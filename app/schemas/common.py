from pydantic import BaseModel, ConfigDict, Field
from typing import Generic, TypeVar, Optional
from datetime import datetime

T = TypeVar("T")


class ErrorResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "Ошибка API"})

    detail: str = Field(description="Текст ошибки")


class MessageResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "Сообщение об успехе"})

    message: str = Field(description="Текст сообщения")


class PaginatedResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(json_schema_extra={"description": "Страница результатов"})

    items: list[T] = Field(description="Элементы страницы")
    total: int = Field(description="Всего записей")
    skip: int = Field(description="Смещение")
    limit: int = Field(description="Размер страницы")


class TimestampMixin(BaseModel):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
