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

    #DB
    database_url: str = "postgresql+psycopg://thor:thor@localhost:5432/thor_db"
    redis_url: str = "redis://localhost:6379/0"
    mongodb_url: str = "mongodb://localhost:27017/thor_db"
    meili_url: str = "http://localhost:7700"
    meili_master_key: str = "dev-meili-key"

    # Keycloak
    keycloak_url: str = "http://localhost:8081"  # host (browser)
    keycloak_internal_url: str = "http://keycloak:8080"  # dentro do docker network
    keycloak_realm: str = "thor"
    keycloak_client_id: str = "thor-api"
    keycloak_verify_audience: bool = True  # valida aud/azp

    cors_origins: list[str] = ["http://localhost:3000"]

settings = Settings()
