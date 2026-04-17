"""
Асинхронное подключение к базе данных PostgreSQL или SQLite.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine,
)
from sqlalchemy.orm import sessionmaker
import os

from app.core.config import settings


class Database:
    """Управление подключением к базе данных"""

    def __init__(self):
        self.engine: AsyncEngine = None
        self.async_session_maker: async_sessionmaker = None

    async def connect(self):
        """Подключение к базе данных"""
        # Используем SQLite для тестирования если PostgreSQL недоступен
        use_sqlite = os.getenv("USE_SQLITE", "false").lower() == "true"
        
        if use_sqlite:
            database_url = "sqlite+aiosqlite:///./messenger.db"
            self.engine = create_async_engine(
                database_url,
                echo=settings.DEBUG,
                connect_args={"check_same_thread": False},
            )
        else:
            try:
                self.engine = create_async_engine(
                    settings.DATABASE_URL,
                    echo=settings.DEBUG,
                    pool_size=settings.DB_POOL_SIZE,
                    max_overflow=settings.DB_MAX_OVERFLOW,
                    pool_pre_ping=True,
                )
            except Exception as e:
                print(f"Warning: Could not connect to PostgreSQL: {e}")
                print("Falling back to SQLite for development")
                database_url = "sqlite+aiosqlite:///./messenger.db"
                self.engine = create_async_engine(
                    database_url,
                    echo=settings.DEBUG,
                    connect_args={"check_same_thread": False},
                )
        
        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

    async def disconnect(self):
        """Отключение от базы данных"""
        if self.engine:
            await self.engine.dispose()

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Получение сессии базы данных"""
        async with self.async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def create_tables(self):
        """Создание таблиц в базе данных"""
        from app.models import Base
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self):
        """Удаление всех таблиц (для тестов)"""
        from app.models import Base
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


# Глобальный экземпляр базы данных
db = Database()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Зависимость для получения сессии БД в API"""
    async for session in db.get_session():
        yield session
