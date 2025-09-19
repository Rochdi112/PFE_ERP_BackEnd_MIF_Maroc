# app/core/config.py

from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "ERP Interventions"
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = Field(default="insecure-test-secret-key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = (
        15  # durée de validité JWT en minutes (15min pour Go-Prod sécurité)
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # durée de validité des refresh tokens
    FILES_ENC_KEY: str = Field(default="")  # clé Fernet pour chiffrement des documents

    # Email SMTP
    SMTP_HOST: str = Field(default="localhost")
    SMTP_PORT: int = Field(default=1025)  # Mailhog/Mailcatcher default
    SMTP_USER: str = Field(default="user")
    SMTP_PASSWORD: str = Field(default="password")
    EMAILS_FROM_EMAIL: str = Field(default="no-reply@example.com")

    # Base de données PostgreSQL
    POSTGRES_DB: str = Field(default="erp_db")
    POSTGRES_USER: str = Field(default="erp_user")
    POSTGRES_PASSWORD: str = Field(default="erp_pass")
    POSTGRES_HOST: str = Field(default="db")
    POSTGRES_PORT: int = Field(default=5432)

    # Répertoire d’upload de fichiers
    UPLOAD_DIRECTORY: str = Field(default="app/static/uploads")

    # CORS
    CORS_ALLOW_ORIGINS: List[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:8000",
        ]
    )
    CORS_ALLOW_METHODS: List[str] = Field(
        default_factory=lambda: ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    )
    CORS_ALLOW_HEADERS: List[str] = Field(
        default_factory=lambda: [
            "Authorization",
            "Content-Type",
            "Accept",
            "Origin",
            "X-Requested-With",
        ]
    )
    CORS_EXPOSE_HEADERS: List[str] = Field(default_factory=lambda: ["X-Request-ID"])
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True)

    # Scheduler toggle
    ENABLE_SCHEDULER: bool = Field(default=False)

    # Environment 
    ENVIRONMENT: str = Field(default="development")  # development, production
    DEBUG: bool = Field(default=False)

    # Logging
    LOG_LEVEL: str = Field(default="INFO")

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Pydantic v2 settings configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # accepte des variables supplémentaires sans lever d'erreur
    )


settings = Settings()
