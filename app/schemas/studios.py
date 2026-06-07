from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime


class StudioCreate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "Создание студии"})

    name: str = Field(min_length=1, max_length=255, description="Полное название")
    short_name: str = Field(
        min_length=1,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Публичный код студии для API, напр. MSK",
    )


class StudioUpdate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "Обновление студии"})

    name: str | None = Field(
        default=None, min_length=1, max_length=255, description="Новое название"
    )


class StudioRead(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "Студия"})

    short_name: str = Field(description="Публичный код")
    name: str = Field(description="Название")
    students_cnt: int = Field(description="Количество студентов")
    created_at: datetime = Field(description="Дата создания")
    updated_at: datetime = Field(description="Дата обновления")

    @classmethod
    def from_studio(cls, studio) -> "StudioRead":
        return cls(
            short_name=studio.short_name,
            name=studio.name,
            students_cnt=studio.students_cnt,
            created_at=studio.created_at,
            updated_at=studio.updated_at,
        )
