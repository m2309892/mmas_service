from pydantic import BaseModel, ConfigDict, Field


class TgLinkRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "Привязка Telegram к студенту"})

    tg_id: int = Field(gt=0, description="Telegram user id")
    mmas_id: str = Field(min_length=1, max_length=255, description="ID студента")


class TgUnlinkRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "Отвязка Telegram от студента"})

    tg_id: int = Field(gt=0, description="Telegram user id")
    mmas_id: str = Field(min_length=1, max_length=255, description="ID студента")


class TgAccountRead(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "Связи Telegram-аккаунта"})

    tg_id: int = Field(description="Telegram user id")
    linked_mmas_ids: list[str] = Field(description="Привязанные mmas_id")
