from __future__ import annotations

from pathlib import Path
from typing import ClassVar, List, Literal, Optional

from pydantic import Field, ValidationError, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR: Path = Path(__file__).resolve().parent.parent
LOGS_DIR_DEFAULT: Path = BASE_DIR / "logs"
MEDIA_DIR_DEFAULT: Path = BASE_DIR / "uploads"
TEMPLATES_DIR_DEFAULT: Path = BASE_DIR / "app" / "templates"
STATIC_DIR_DEFAULT: Path = BASE_DIR / "app" / "static"


class Settings(BaseSettings):
    MODE: Literal["DEV", "TEST", "PROD"] = Field(..., description="Окружение")
    APP_VERSION: str = Field("0.0.1", description="Версия приложения")
    BASE_SITE_URL: str = Field(..., description="Базовый URL сайта (ссылки, CORS при необходимости)")

    SECRET_KEY: str = Field(..., description="Секрет подписи access JWT")
    REFRESH_SECRET_KEY: str = Field(..., description="Секрет подписи refresh JWT")
    ALGORITHM: str = Field("HS256", description="Алгоритм JWT")
    JWT_ACCESS_EXPIRE_MINUTES: int = Field(60, ge=1, le=24 * 60, description="Срок access JWT (мин.)")
    JWT_REFRESH_EXPIRE_DAYS: int = Field(30, ge=1, le=365, description="Срок refresh JWT (дн.)")

    HOST: str = Field("0.0.0.0", description="Bind host")
    PORT: int = Field(8015, ge=1, le=65535, description="Bind port")
    WEB_CONCURRENCY: int = Field(4, ge=1, le=64, description="Воркеры Gunicorn / подсказка для деплоя")
    TIMEOUT: int = Field(120, ge=1, le=3600, description="Таймаут запроса/воркера (сек.)")
    RELOAD: bool = Field(False, description="Uvicorn reload (только DEV)")
    PROXY_HEADERS: bool = Field(True, description="Доверять заголовкам reverse proxy")

    ENABLE_DOCS: bool = Field(True, description="/docs, /redoc, /openapi.json")
    ENABLE_HSTS: bool = Field(False, description="HSTS (только за HTTPS)")

    CORS_ORIGINS: List[str] = Field(
        default_factory=lambda: [
            "http://localhost",
            "http://localhost:8000",
            "http://127.0.0.1",
            "http://127.0.0.1:8000",
        ],
        description="Разрешённые Origin для CORS",
    )

    LOG_DIR: str = Field(default=str(LOGS_DIR_DEFAULT), description="Каталог логов")
    MEDIA_DIR: str = Field(default=str(MEDIA_DIR_DEFAULT), description="Медиа")
    STATIC_DIR: str = Field(default=str(STATIC_DIR_DEFAULT), description="Статика")
    TEMPLATES_DIR: str = Field(default=str(TEMPLATES_DIR_DEFAULT), description="Шаблоны Jinja2")
    BASE_DIR: Path = Path(__file__).resolve().parent.parent

    DB_HOST: str = Field(..., description="Postgres host")
    DB_PORT: int = Field(..., ge=1, le=65535, description="Postgres port")
    DB_USER: str = Field(..., description="Postgres user")
    DB_PASS: str = Field(..., description="Postgres password")
    DB_NAME: str = Field(..., description="Postgres database")

    DATABASE_URL: Optional[str] = Field(
        default=None,
        description="Полный async DSN; если не задан — собирается из DB_*",
    )

    DB_POOL_SIZE: int = Field(10, description="SQLAlchemy pool size")
    DB_MAX_OVERFLOW: int = Field(5, description="SQLAlchemy max overflow")
    DB_POOL_TIMEOUT: int = Field(30, description="SQLAlchemy pool timeout")
    DB_POOL_RECYCLE: int = Field(1800, description="Pool recycle (сек.)")
    DB_POOL_PRE_PING: bool = Field(True, description="Pool pre-ping")

    REDIS_HOST: str = Field(..., description="Redis host")
    REDIS_PORT: int = Field(..., ge=1, le=65535, description="Redis port")
    REDIS_DB: int = Field(0, ge=0, description="Redis DB index")
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis AUTH (если включён)")

    CELERY_BROKER_URL: Optional[str] = Field(default=None, description="Celery broker")
    CELERY_RESULT_BACKEND: Optional[str] = Field(default=None, description="Celery results")

    @model_validator(mode="before")
    @classmethod
    def compute_database_url(cls, values: dict) -> dict:
        if not values.get("DATABASE_URL"):
            required = ("DB_USER", "DB_PASS", "DB_HOST", "DB_PORT", "DB_NAME")
            if all(k in values and values[k] not in (None, "") for k in required):
                values["DATABASE_URL"] = (
                    f"postgresql+asyncpg://{values['DB_USER']}:{values['DB_PASS']}"
                    f"@{values['DB_HOST']}:{values['DB_PORT']}/{values['DB_NAME']}"
                )
        return values

    @model_validator(mode="before")
    @classmethod
    def compute_celery_urls(cls, values: dict) -> dict:
        if not values.get("CELERY_BROKER_URL"):
            host = values.get("REDIS_HOST")
            port = values.get("REDIS_PORT")
            db = values.get("REDIS_DB", 0)
            if host and port is not None:
                values["CELERY_BROKER_URL"] = f"redis://{host}:{port}/{db}"
        if not values.get("CELERY_RESULT_BACKEND"):
            values["CELERY_RESULT_BACKEND"] = values.get("CELERY_BROKER_URL")
        return values

    @model_validator(mode="after")
    def validate_paths(self) -> "Settings":
        self.LOG_DIR = str(Path(self.LOG_DIR).resolve())
        self.MEDIA_DIR = str(Path(self.MEDIA_DIR).resolve())
        self.STATIC_DIR = str(Path(self.STATIC_DIR).resolve())
        self.TEMPLATES_DIR = str(Path(self.TEMPLATES_DIR).resolve())
        if self.MODE == "PROD" and self.RELOAD:
            self.RELOAD = False
        return self

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def SYNC_DATABASE_URL(self) -> str:
        if not self.DATABASE_URL:
            raise RuntimeError("DATABASE_URL is not set")
        return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg://")


MEDIA_DIR = str(MEDIA_DIR_DEFAULT)

try:
    settings = Settings()
except ValidationError as e:
    missing = [err["loc"] for err in e.errors()]
    raise RuntimeError(
        f"Invalid environment configuration. Missing/malformed: {missing}"
    ) from e
