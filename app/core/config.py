from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Основные настройки
    app_name: str = "MMAS Service"
    debug: bool = False
    
    # База данных
    database_url: str
    database_echo: bool = False
    
    # JWT настройки
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Бот настройки
    bot_token: str
    webhook_url: Optional[str] = None
    webhook_path: str = "/webhook"
    
    # Redis (для кеширования и сессий бота)
    redis_url: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Создаем экземпляр настроек
settings = Settings()
