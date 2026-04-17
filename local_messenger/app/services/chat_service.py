"""
Сервисы для работы с чатами и сообщениями.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, update, delete, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.models import (
    Chat, ChatMember, Message, Media, Reaction, ReadReceipt,
    ChatType, MemberRole, MessageType
)
from app.core.config import settings


class ChatService:
    """Сервис для управления чатами"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def get_by_id(self, chat_id: UUID) -> Optional[Chat]:
        """Получение чата по ID"""
        result = await self.db.execute(
            select(Chat)
            .options(selectinload(Chat.members).joinedload(ChatMember.user))
            .where(Chat.id == chat_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        chat_type: ChatType,
        owner_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        member_ids: Optional[List[UUID]] = None,
        max_participants: int = 200,
        is_read_only: bool = False,
    ) -> Chat:
        """Создание нового чата"""
        chat = Chat(
            chat_type=chat_type,
            name=name,
            description=description,
            owner_id=owner_id,
            max_participants=max_participants,
            is_read_only=is_read_only,
        )
        self.db.add(chat)
        await self.db.flush()

        # Добавляем владельца как участника с ролью owner
        owner_member = ChatMember(
            chat_id=chat.id,
            user_id=owner_id,
            role=MemberRole.OWNER,
        )
        self.db.add(owner_member)

        # Добавляем остальных участников
        if member_ids:
            for user_id in member_ids:
                if user_id != owner_id:
                    member = ChatMember(
                        chat_id=chat.id,
                        user_id=user_id,
                        role=MemberRole.MEMBER,
                    )
                    self.db.add(member)

        await self.db.flush()
        await self.db.refresh(chat)
        return chat

    async def get_user_chats(self, user_id: UUID) -> List[Chat]:
        """Получение всех чатов пользователя"""
        result = await self.db.execute(
            select(Chat)
            .join(ChatMember)
            .where(ChatMember.user_id == user_id)
            .options(selectinload(Chat.members))
            .order_by(Chat.updated_at.desc())
        )
        return result.scalars().all()

    async def add_member(
        self,
        chat_id: UUID,
        user_id: UUID,
        role: MemberRole = MemberRole.MEMBER,
    ) -> ChatMember:
        """Добавление участника в чат"""
        member = ChatMember(
            chat_id=chat_id,
            user_id=user_id,
            role=role,
        )
        self.db.add(member)
        await self.db.flush()
        await self.db.refresh(member)
        return member

    async def remove_member(self, chat_id: UUID, user_id: UUID) -> bool:
        """Удаление участника из чата"""
        await self.db.execute(
            delete(ChatMember)
            .where(ChatMember.chat_id == chat_id)
            .where(ChatMember.user_id == user_id)
        )
        return True

    async def update_member_role(
        self,
        chat_id: UUID,
        user_id: UUID,
        role: MemberRole,
    ) -> bool:
        """Обновление роли участника"""
        await self.db.execute(
            update(ChatMember)
            .where(ChatMember.chat_id == chat_id)
            .where(ChatMember.user_id == user_id)
            .values(role=role)
        )
        return True

    async def get_member(self, chat_id: UUID, user_id: UUID) -> Optional[ChatMember]:
        """Получение участника чата"""
        result = await self.db.execute(
            select(ChatMember)
            .where(ChatMember.chat_id == chat_id)
            .where(ChatMember.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def delete(self, chat_id: UUID) -> bool:
        """Удаление чата"""
        await self.db.execute(
            delete(Chat).where(Chat.id == chat_id)
        )
        return True


class MessageService:
    """Сервис для управления сообщениями"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def create(
        self,
        chat_id: UUID,
        sender_id: UUID,
        content: Optional[str] = None,
        message_type: MessageType = MessageType.TEXT,
        reply_to_id: Optional[UUID] = None,
        forwarded_from_id: Optional[UUID] = None,
    ) -> Message:
        """Создание нового сообщения"""
        message = Message(
            chat_id=chat_id,
            sender_id=sender_id,
            content=content,
            message_type=message_type,
            reply_to_id=reply_to_id,
            forwarded_from_id=forwarded_from_id,
        )
        self.db.add(message)
        await self.db.flush()
        await self.db.refresh(message)

        # Обновляем время обновления чата
        await self.db.execute(
            update(Chat)
            .where(Chat.id == chat_id)
            .values(updated_at=datetime.utcnow())
        )

        return message

    async def get_by_id(self, message_id: UUID) -> Optional[Message]:
        """Получение сообщения по ID"""
        result = await self.db.execute(
            select(Message)
            .options(
                selectinload(Message.sender),
                selectinload(Message.media),
                selectinload(Message.reactions).joinedload(Reaction.user),
            )
            .where(Message.id == message_id)
        )
        return result.scalar_one_or_none()

    async def get_chat_messages(
        self,
        chat_id: UUID,
        limit: int = 50,
        offset: int = 0,
        before_id: Optional[UUID] = None,
    ) -> List[Message]:
        """Получение сообщений чата с пагинацией"""
        query = (
            select(Message)
            .options(
                selectinload(Message.sender),
                selectinload(Message.media),
                selectinload(Message.reactions),
            )
            .where(Message.chat_id == chat_id)
            .where(Message.deleted_at.is_(None))
            .order_by(Message.created_at.desc())
        )

        if before_id:
            subquery = select(Message.created_at).where(Message.id == before_id)
            before_time = (await self.db.execute(subquery)).scalar()
            if before_time:
                query = query.where(Message.created_at < before_time)

        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update(
        self,
        message_id: UUID,
        content: str,
    ) -> Optional[Message]:
        """Редактирование сообщения (в течение 48 часов)"""
        message = await self.get_by_id(message_id)
        if not message:
            return None

        # Проверка: можно редактировать только в течение 48 часов
        if datetime.utcnow() - message.created_at > timedelta(hours=settings.MESSAGE_EDIT_TIMEOUT_HOURS):
            raise ValueError("Message edit timeout exceeded")

        await self.db.execute(
            update(Message)
            .where(Message.id == message_id)
            .values(
                content=content,
                edited_at=datetime.utcnow(),
            )
        )
        await self.db.flush()
        return await self.get_by_id(message_id)

    async def delete(self, message_id: UUID) -> bool:
        """Удаление сообщения (мягкое удаление)"""
        await self.db.execute(
            update(Message)
            .where(Message.id == message_id)
            .values(deleted_at=datetime.utcnow())
        )
        return True

    async def pin(self, message_id: UUID) -> bool:
        """Закрепить сообщение"""
        await self.db.execute(
            update(Message)
            .where(Message.id == message_id)
            .values(is_pinned=True)
        )
        return True

    async def unpin(self, message_id: UUID) -> bool:
        """Открепить сообщение"""
        await self.db.execute(
            update(Message)
            .where(Message.id == message_id)
            .values(is_pinned=False)
        )
        return True

    async def add_reaction(
        self,
        message_id: UUID,
        user_id: UUID,
        emoji: str,
    ) -> Reaction:
        """Добавление реакции к сообщению"""
        # Проверяем существующую реакцию
        existing = await self.db.execute(
            select(Reaction)
            .where(Reaction.message_id == message_id)
            .where(Reaction.user_id == user_id)
        )
        existing_reaction = existing.scalar_one_or_none()

        if existing_reaction:
            # Обновляем существующую реакцию
            await self.db.execute(
                update(Reaction)
                .where(Reaction.id == existing_reaction.id)
                .values(emoji=emoji)
            )
            await self.db.flush()
            return existing_reaction

        reaction = Reaction(
            message_id=message_id,
            user_id=user_id,
            emoji=emoji,
        )
        self.db.add(reaction)
        await self.db.flush()
        await self.db.refresh(reaction)
        return reaction

    async def remove_reaction(self, message_id: UUID, user_id: UUID) -> bool:
        """Удаление реакции"""
        await self.db.execute(
            delete(Reaction)
            .where(Reaction.message_id == message_id)
            .where(Reaction.user_id == user_id)
        )
        return True

    async def mark_as_read(self, message_id: UUID, user_id: UUID) -> ReadReceipt:
        """Отметить сообщение как прочитанное"""
        # Проверяем существующий receipt
        existing = await self.db.execute(
            select(ReadReceipt)
            .where(ReadReceipt.message_id == message_id)
            .where(ReadReceipt.user_id == user_id)
        )
        if existing.scalar_one_or_none():
            return None

        receipt = ReadReceipt(
            message_id=message_id,
            user_id=user_id,
        )
        self.db.add(receipt)
        await self.db.flush()
        await self.db.refresh(receipt)
        return receipt

    async def search(
        self,
        chat_id: Optional[UUID],
        query: str,
        sender_id: Optional[UUID] = None,
        message_type: Optional[MessageType] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Message], int]:
        """Поиск сообщений"""
        conditions = [Message.deleted_at.is_(None)]

        if chat_id:
            conditions.append(Message.chat_id == chat_id)
        if sender_id:
            conditions.append(Message.sender_id == sender_id)
        if message_type:
            conditions.append(Message.message_type == message_type)
        if date_from:
            conditions.append(Message.created_at >= date_from)
        if date_to:
            conditions.append(Message.created_at <= date_to)

        # Полнотекстовый поиск (PostgreSQL)
        if query:
            from sqlalchemy import text
            conditions.append(
                text("search_vector @@ plainto_tsquery('russian', :query)")
            )

        # Основной запрос
        count_query = select(func.count()).select_from(Message).where(*conditions)
        total = (await self.db.execute(count_query)).scalar()

        messages_query = (
            select(Message)
            .options(selectinload(Message.sender), selectinload(Message.media))
            .where(*conditions)
            .order_by(Message.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        if query:
            messages_query = messages_query.params(query=query)

        result = await self.db.execute(messages_query)
        messages = result.scalars().all()

        return messages, total
