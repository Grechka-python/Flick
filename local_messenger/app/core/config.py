"""
Конфигурация приложения.
Загружает настройки из переменных окружения.
"""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения"""

    # Приложение
    APP_NAME: str = "Local Messenger"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Сервер
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4

    # База данных PostgreSQL
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "messenger"
    DB_USER: str = "messenger_user"
    DB_PASSWORD: str = "secure_password"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def SYNC_DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # MinIO (объектное хранилище)
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "media"
    MINIO_SECURE: bool = False

    # JWT токены
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # TOTP (2FA)
    TOTP_ISSUER: str = "Local Messenger"
    TOTP_ALGORITHM: str = "SHA1"
    TOTP_DIGITS: int = 6
    TOTP_PERIOD: int = 30

    # Безопасность
    PASSWORD_MIN_LENGTH: int = 8
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15

    # Ограничения файлов
    MAX_FILE_SIZE: int = 2 * 1024 * 1024 * 1024  # 2 GB
    ALLOWED_FILE_TYPES: list = [
        # Изображения
        "image/jpeg", "image/png", "image/gif", "image/webp", "image/bmp",
        # Видео
        "video/mp4", "video/x-msvideo", "video/quicktime", "video/x-matroska",
        # Аудио
        "audio/mpeg", "audio/wav", "audio/ogg", "audio/aac",
        # Документы
        "application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/plain", "application/zip", "application/x-rar-compressed",
    ]

    # Лимиты
    MAX_GROUP_PARTICIPANTS: int = 200
    DEFAULT_STORAGE_QUOTA: int = 10 * 1024 * 1024 * 1024  # 10 GB
    MESSAGE_EDIT_TIMEOUT_HOURS: int = 48
    MAX_REACTIONS_PER_MESSAGE: int = 10

    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_CONNECTION_TIMEOUT: int = 300

    # Логирование
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Redis (для кэширования и pub/sub)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Звонки (WebRTC signaling)
    SIGNALING_SERVER_URL: str = "ws://localhost:8001"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Получить кэшированные настройки"""
    return Settings()


# Глобальный экземпляр настроек
settings = get_settings()
