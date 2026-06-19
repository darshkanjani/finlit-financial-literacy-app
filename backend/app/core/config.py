"""
Central application configuration.

Settings are read from environment variables and an optional local `.env` file.
Do not hardcode secrets in source code.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Environment
    ENV: str = "dev"
    RETURN_RESET_TOKEN_IN_RESPONSE: bool = False

    # Database
    DATABASE_URL: str = "sqlite:///./finlit.db"

    # JWT
    JWT_SECRET: str = "dev-secret-change-me"
    JWT_ALG: str = "HS256"
    JWT_EXPIRES_MINUTES: int = 60 * 24

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # LLM
    LLM_API_KEY: str | None = None
    LLM_PROVIDER: str = "openai"

    # Optional email settings for password reset
    MAIL_USERNAME: str | None = None
    MAIL_PASSWORD: str | None = None
    MAIL_FROM: str | None = None
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    MAIL_USE_CREDENTIALS: bool = True


settings = Settings()
