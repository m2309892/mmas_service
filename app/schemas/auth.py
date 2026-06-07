from pydantic import BaseModel, ConfigDict, Field


class StaffLoginRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "Вход staff-пользователя"})

    username: str = Field(min_length=3, max_length=100, description="Логин admin или trainer")
    password: str = Field(min_length=6, max_length=128, description="Пароль")


class StudentLoginRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "Вход студента"})

    mmas_id: str = Field(min_length=1, max_length=255, description="Публичный ID студента")
    password: str = Field(min_length=6, max_length=128, description="Пароль")


class RefreshTokenRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "Обновление JWT"})

    refresh_token: str = Field(description="Refresh token из предыдущего ответа login")


class TokenResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "Пара access/refresh JWT"})

    access_token: str = Field(description="JWT для Authorization: Bearer")
    refresh_token: str = Field(description="JWT для /api/auth/refresh")
    token_type: str = Field(default="bearer", description="Тип токена")
    role: str = Field(description="admin, trainer или student")
    studio_short_names: list[str] = Field(
        default_factory=list,
        description="Студии trainer (пусто для admin/student)",
    )
