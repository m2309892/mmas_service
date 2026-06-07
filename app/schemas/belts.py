from pydantic import BaseModel, ConfigDict, Field


class BeltCreate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "Создание пояса"})

    code: str = Field(
        min_length=1,
        max_length=50,
        pattern=r"^[a-z0-9_-]+$",
        description="Публичный код пояса, напр. white",
    )
    color: str = Field(min_length=1, max_length=255, description="Цвет пояса")
    style: str | None = Field(default=None, max_length=100, description="Стиль (BJJ, карате…)")
    sort_order: int = Field(default=0, ge=0, description="Порядок в списке")


class BeltUpdate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "Обновление пояса"})

    color: str | None = Field(default=None, min_length=1, max_length=255, description="Цвет")
    style: str | None = Field(default=None, max_length=100, description="Стиль")
    sort_order: int | None = Field(default=None, ge=0, description="Порядок сортировки")


class BeltRead(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "Пояс"})

    code: str = Field(description="Публичный код")
    color: str = Field(description="Цвет")
    style: str | None = Field(description="Стиль")
    sort_order: int = Field(description="Порядок сортировки")

    @classmethod
    def from_belt(cls, belt) -> "BeltRead":
        return cls(
            code=belt.code,
            color=belt.color,
            style=belt.style,
            sort_order=belt.sort_order,
        )
