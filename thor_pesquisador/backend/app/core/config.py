from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Thor Pesquisador"
    app_env: str = "dev"
    database_url: str = "postgresql+psycopg://thor:thor@postgres:5432/thor_pesquisador"
    mongodb_url: str = "mongodb://mongo:27017/thor_pesquisador"
    mongodb_database: str = "thor_pesquisador"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    public_app_url: str = "http://localhost:3000"
    session_cookie_name: str = "thor_pesquisador_session"
    session_cookie_domain: str | None = None
    session_cookie_secure: bool = False
    app_session_secret: str = "dev-change-me"
    govbr_authorize_url: str = "https://sso.staging.acesso.gov.br/authorize"
    govbr_token_url: str = "https://sso.staging.acesso.gov.br/token"
    govbr_jwks_url: str = "https://sso.staging.acesso.gov.br/jwk"
    govbr_client_id: str = "change-me"
    govbr_client_secret: str = "change-me"
    govbr_redirect_uri: str = "http://localhost:8000/api/v1/auth/govbr/callback"
    govbr_dev_login: bool = True
    dev_admin_enabled: bool = False
    auth_disabled_for_tests: bool = False
    redis_url: str = "redis://redis:6379/0"
    indexacao_queue_name: str = "thor_pesquisador:indexacao"
    meilisearch_url: str = "http://meilisearch:7700"
    meilisearch_api_key: str = "dev-master-key"
    indexacao_batch_size: int = 500
    s3_endpoint_url: str = ""
    s3_bucket: str = ""
    s3_region: str = "us-east-1"
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""
    s3_force_path_style: bool = True
    s3_url_expiration: int = Field(default=300, ge=1, le=3600)
    upload_max_bytes: int = Field(default=20 * 1024 * 1024, ge=1)
    upload_allowed_mime_types: list[str] = Field(default_factory=lambda: ["image/jpeg", "image/png", "image/tiff", "image/webp"])


settings = Settings()
