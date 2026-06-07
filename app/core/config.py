from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    app_name: str = "MMAS Service"
    debug: bool = False

    database_url: str
    database_echo: bool = False

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    admin_bootstrap_username: Optional[str] = None
    admin_bootstrap_password: Optional[str] = None

    log_json: bool = False


settings = Settings()
