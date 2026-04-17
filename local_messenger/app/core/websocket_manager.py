"""
WebSocket менеджер для real-time обновлений.
Управляет подключениями клиентов и рассылкой сообщений.
"""

import asyncio
import json
from typing import Dict, List, Set
from uuid import UUID

from fastapi import WebSocket


class ConnectionManager:
    """Менеджер WebSocket подключений"""

    def __init__(self):
        # Активные подключения: {user_id: websocket}
        self.active_connections: Dict[UUID, WebSocket] = {}
        # Подписки на чаты: {chat_id: set of user_ids}
        self.chat_subscriptions: Dict[UUID, Set[UUID]] = {}
        # Блокировки для потокобезопасности
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_id: UUID) -> bool:
        """Подключение пользователя к WebSocket"""
        await websocket.accept()
        async with self._lock:
            if user_id in self.active_connections:
                # Отключаем старое подключение если есть
                old_ws = self.active_connections[user_id]
                try:
                    await old_ws.close()
                except:
                    pass
            self.active_connections[user_id] = websocket
        return True

    def disconnect(self, user_id: UUID):
        """Отключение пользователя"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        # Удаляем из всех подписок
        for chat_id in list(self.chat_subscriptions.keys()):
            if user_id in self.chat_subscriptions.get(chat_id, set()):
                self.chat_subscriptions[chat_id].discard(user_id)

    async def subscribe_to_chat(self, user_id: UUID, chat_id: UUID):
        """Подписка пользователя на обновления чата"""
        async with self._lock:
            if chat_id not in self.chat_subscriptions:
                self.chat_subscriptions[chat_id] = set()
            self.chat_subscriptions[chat_id].add(user_id)

    async def unsubscribe_from_chat(self, user_id: UUID, chat_id: UUID):
        """Отписка от обновлений чата"""
        async with self._lock:
            if chat_id in self.chat_subscriptions:
                self.chat_subscriptions[chat_id].discard(user_id)
                if not self.chat_subscriptions[chat_id]:
                    del self.chat_subscriptions[chat_id]

    async def send_personal_message(self, user_id: UUID, message: dict):
        """Отправка персонального сообщения пользователю"""
        async with self._lock:
            websocket = self.active_connections.get(user_id)
        if websocket:
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"Error sending message to {user_id}: {e}")
                await self.disconnect_socket(user_id)

    async def broadcast_to_chat(self, chat_id: UUID, message: dict):
        """Рассылка сообщения всем участникам чата"""
        async with self._lock:
            subscriber_ids = list(self.chat_subscriptions.get(chat_id, set()))

        for user_id in subscriber_ids:
            await self.send_personal_message(user_id, message)

    async def broadcast_online_status(self, user_id: UUID, is_online: bool):
        """Рассылка статуса онлайн/оффлайн всем кто подписан на чаты с этим пользователем"""
        event_type = "user_online" if is_online else "user_offline"
        message = {
            "type": event_type,
            "payload": {
                "user_id": str(user_id),
                "is_online": is_online,
            }
        }

        # Находим все чаты где есть этот пользователь
        async with self._lock:
            for chat_id, subscribers in self.chat_subscriptions.items():
                if user_id in subscribers:
                    for subscriber_id in subscribers:
                        if subscriber_id != user_id:
                            await self.send_personal_message(subscriber_id, message)

    async def send_typing_status(self, chat_id: UUID, user_id: UUID, is_typing: bool):
        """Отправка статуса набора текста"""
        message = {
            "type": "typing_status",
            "payload": {
                "chat_id": str(chat_id),
                "user_id": str(user_id),
                "is_typing": is_typing,
            }
        }
        # Отправляем всем кроме того кто печатает
        async with self._lock:
            subscriber_ids = list(self.chat_subscriptions.get(chat_id, set()))

        for subscriber_id in subscriber_ids:
            if subscriber_id != user_id:
                await self.send_personal_message(subscriber_id, message)

    async def disconnect_socket(self, user_id: UUID):
        """Закрытие WebSocket подключения"""
        async with self._lock:
            websocket = self.active_connections.pop(user_id, None)
        if websocket:
            try:
                await websocket.close()
            except:
                pass
        self.disconnect(user_id)

    def get_online_users(self) -> List[UUID]:
        """Получение списка онлайн пользователей"""
        return list(self.active_connections.keys())

    def is_user_online(self, user_id: UUID) -> bool:
        """Проверка онлайн ли пользователь"""
        return user_id in self.active_connections


# Глобальный экземпляр менеджера подключений
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, user_id: UUID):
    """
    WebSocket эндпоинт для real-time обновлений.
    Используется в main.py через Depends.
    """
    connected = await manager.connect(websocket, user_id)
    if not connected:
        return

    # Отправляем событие онлайн
    await manager.broadcast_online_status(user_id, is_online=True)

    try:
        while True:
            # Получаем сообщения от клиента
            data = await websocket.receive_text()
            message = json.loads(data)

            # Обработка входящих событий
            event_type = message.get("type")
            payload = message.get("payload", {})

            if event_type == "send_message":
                # Клиент отправил сообщение через WebSocket
                # В реальном приложении здесь будет логика сохранения и рассылки
                await manager.broadcast_to_chat(
                    UUID(payload.get("chat_id")),
                    {
                        "type": "new_message",
                        "payload": payload,
                    }
                )

            elif event_type == "typing_start":
                await manager.send_typing_status(
                    UUID(payload.get("chat_id")),
                    user_id,
                    is_typing=True,
                )

            elif event_type == "typing_stop":
                await manager.send_typing_status(
                    UUID(payload.get("chat_id")),
                    user_id,
                    is_typing=False,
                )

            elif event_type == "mark_read":
                # Отправка подтверждения прочтения
                await manager.broadcast_to_chat(
                    UUID(payload.get("chat_id")),
                    {
                        "type": "read_receipt",
                        "payload": {
                            "message_id": payload.get("message_id"),
                            "user_id": str(user_id),
                        },
                    }
                )

            elif event_type == "subscribe_chat":
                await manager.subscribe_to_chat(
                    user_id,
                    UUID(payload.get("chat_id")),
                )

            elif event_type == "unsubscribe_chat":
                await manager.unsubscribe_from_chat(
                    user_id,
                    UUID(payload.get("chat_id")),
                )

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error for user {user_id}: {e}")
    finally:
        await manager.broadcast_online_status(user_id, is_online=False)
        manager.disconnect(user_id)
