"""
Configurações globais da aplicação.
Lê variáveis de ambiente a partir do arquivo .env.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/license_system"
    SECRET_KEY: str = "change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    CLIENT_TOKEN_EXPIRE_MINUTES: int = 1440
    ONLINE_THRESHOLD_SECONDS: int = 90
    ENVIRONMENT: str = "production"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
