"""
Главное приложение FastAPI.
Точка входа для сервера мессенджера.
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from app.core.config import settings
from app.db.session import db
from app.api.routes import router
from app.core.websocket_manager import manager, websocket_endpoint


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    await db.connect()
    print("Database connected")

    # Создаём таблицы если не существуют (для разработки)
    if settings.DEBUG:
        await db.create_tables()
        print("Database tables created")

    yield

    # Shutdown
    print("Shutting down...")
    await db.disconnect()
    print("Database disconnected")


# Создание приложения
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Локальный мессенджер с функционалом Telegram",
    lifespan=lifespan,
)

# CORS middleware (для веб-клиента)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене нужно ограничить
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(router, prefix="/api/v1")

# Монтирование статических файлов (для GUI)
# app.mount("/static", StaticFiles(directory="app/static"), name="static")


# WebSocket эндпоинт
@app.websocket("/ws")
async def websocket_connect(websocket: WebSocket):
    """
    WebSocket подключение для real-time обновлений.
    Клиент должен передать токен авторизации при подключении.
    """
    # Получаем токен из query параметров или заголовков
    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=4001, reason="Token required")
        return

    # Декодируем токен для получения user_id
    from app.core.security import decode_token
    payload = decode_token(token)

    if not payload:
        await websocket.close(code=4002, reason="Invalid token")
        return

    from uuid import UUID
    user_id = UUID(payload.get("sub"))

    # Запускаем обработчик WebSocket
    await websocket_endpoint(websocket, user_id)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


# Главная страница (для веба)
@app.get("/")
async def root():
    """Информация о API"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=settings.WORKERS if not settings.DEBUG else 1,
    )
