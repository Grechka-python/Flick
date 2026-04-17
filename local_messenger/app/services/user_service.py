"""
Сервисы для работы с пользователями.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import User, Session, ChatMember, Chat
from app.core.security import get_password_hash, verify_password


class UserService:
    """Сервис для управления пользователями"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Получение пользователя по ID"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        """Получение пользователя по имени пользователя"""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        username: str,
        password: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        storage_quota: Optional[int] = None,
    ) -> User:
        """Создание нового пользователя"""
        hashed_password = get_password_hash(password)
        user = User(
            username=username,
            password_hash=hashed_password,
            email=email,
            phone=phone,
            storage_quota=storage_quota,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update(
        self,
        user_id: UUID,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> Optional[User]:
        """Обновление данных пользователя"""
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                email=email,
                phone=phone,
                avatar_url=avatar_url,
            )
        )
        await self.db.flush()
        return await self.get_by_id(user_id)

    async def update_password(self, user_id: UUID, new_password: str) -> bool:
        """Обновление пароля"""
        hashed_password = get_password_hash(new_password)
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(password_hash=hashed_password)
        )
        return True

    async def set_totp_secret(self, user_id: UUID, secret: str) -> bool:
        """Установка секрета TOTP"""
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(totp_secret=secret)
        )
        return True

    async def update_last_seen(self, user_id: UUID) -> bool:
        """Обновление времени последнего посещения"""
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_seen=datetime.utcnow())
        )
        return True

    async def delete(self, user_id: UUID) -> bool:
        """Удаление пользователя"""
        await self.db.execute(
            delete(User).where(User.id == user_id)
        )
        return True

    async def search(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
    ) -> List[User]:
        """Поиск пользователей по имени"""
        result = await self.db.execute(
            select(User)
            .where(User.username.ilike(f"%{query}%"))
            .where(User.is_active == True)
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def get_storage_usage(self, user_id: UUID) -> int:
        """Получение использованного места пользователем"""
        # Запрос к таблице media для подсчёта общего размера файлов
        from app.models import Media, Message
        result = await self.db.execute(
            select(Media.file_size)
            .join(Message, Media.message_id == Message.id)
            .where(Message.sender_id == user_id)
        )
        files = result.scalars().all()
        return sum(files) if files else 0


class SessionService:
    """Сервис для управления сессиями"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def create(
        self,
        user_id: UUID,
        device_name: str,
        device_type: str,
        ip_address: str,
        access_token_hash: str,
        refresh_token_hash: str,
        expires_at: datetime,
    ) -> Session:
        """Создание новой сессии"""
        session = Session(
            user_id=user_id,
            device_name=device_name,
            device_type=device_type,
            ip_address=ip_address,
            access_token_hash=access_token_hash,
            refresh_token_hash=refresh_token_hash,
            expires_at=expires_at,
        )
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def get_by_id(self, session_id: UUID) -> Optional[Session]:
        """Получение сессии по ID"""
        result = await self.db.execute(
            select(Session).where(Session.id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_all_for_user(self, user_id: UUID) -> List[Session]:
        """Получение всех активных сессий пользователя"""
        result = await self.db.execute(
            select(Session)
            .where(Session.user_id == user_id)
            .where(Session.is_active == True)
            .order_by(Session.last_activity.desc())
        )
        return result.scalars().all()

    async def deactivate(self, session_id: UUID) -> bool:
        """Деактивация сессии"""
        await self.db.execute(
            update(Session)
            .where(Session.id == session_id)
            .values(is_active=False)
        )
        return True

    async def deactivate_all_for_user(self, user_id: UUID) -> bool:
        """Деактивация всех сессий пользователя"""
        await self.db.execute(
            update(Session)
            .where(Session.user_id == user_id)
            .values(is_active=False)
        )
        return True

    async def update_activity(self, session_id: UUID) -> bool:
        """Обновление времени последней активности"""
        await self.db.execute(
            update(Session)
            .where(Session.id == session_id)
            .values(last_activity=datetime.utcnow())
        )
        return True
