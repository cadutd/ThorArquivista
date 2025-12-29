from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "dev"
    app_name: str = "Thor Gestor de Arquivos Digitais"
    database_url: str = "postgresql+psycopg://thor:thor@localhost:5432/thor_db"

settings = Settings()
