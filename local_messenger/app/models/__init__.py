"""
Модели базы данных для локального мессенджера.
Используется SQLAlchemy с асинхронной поддержкой.
Поддержка PostgreSQL и SQLite.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID, uuid4
import os

from sqlalchemy import (
    Column, String, Text, Boolean, BigInteger, Integer,
    ForeignKey, DateTime, UniqueConstraint, Index, Enum as SQLEnum, CHAR
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, INET, TSVECTOR
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


# Определяем тип UUID в зависимости от БД
use_sqlite = os.getenv("USE_SQLITE", "false").lower() == "true"
if use_sqlite:
    # Для SQLite используем CHAR(36) для хранения UUID как строки
    def GUID():
        return CHAR(36)
    # Для SQLite используем TEXT для IP адресов
    def IP_ADDRESS():
        return Text
    # Для SQLite не используем полнотекстовый поиск
    def SEARCH_VECTOR():
        return Text
else:
    # Для PostgreSQL используем родной UUID тип
    def GUID():
        return PGUUID(as_uuid=True)
    # Для PostgreSQL используем родной INET тип
    def IP_ADDRESS():
        return INET
    # Для PostgreSQL используем полнотекстовый поиск
    def SEARCH_VECTOR():
        return TSVECTOR


class ChatType(str, Enum):
    PRIVATE = "private"
    GROUP = "group"
    CHANNEL = "channel"


class DeviceType(str, Enum):
    DESKTOP = "desktop"
    MOBILE = "mobile"
    WEB = "web"


class MemberRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"


class User(Base):
    """Таблица пользователей"""
    __tablename__ = "users"

    id = Column(GUID(), primary_key=True, default=uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(255))
    phone = Column(String(20))
    avatar_url = Column(Text)
    totp_secret = Column(String(255))
    is_active = Column(Boolean, default=True)
    storage_quota = Column(BigInteger, default=10737418240)  # 10 GB
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True))

    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    owned_chats = relationship("Chat", back_populates="owner", foreign_keys="Chat.owner_id")
    memberships = relationship("ChatMember", back_populates="user", cascade="all, delete-orphan")
    sent_messages = relationship("Message", back_populates="sender", foreign_keys="Message.sender_id")
    reactions = relationship("Reaction", back_populates="user", cascade="all, delete-orphan")
    read_receipts = relationship("ReadReceipt", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


class Session(Base):
    """Таблица сессий пользователей"""
    __tablename__ = "sessions"

    id = Column(GUID(), primary_key=True, default=uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    device_name = Column(String(100))
    device_type = Column(SQLEnum(DeviceType))
    ip_address = Column(IP_ADDRESS())
    access_token_hash = Column(String(255), nullable=False)
    refresh_token_hash = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", back_populates="sessions")

    __table_args__ = (
        Index("idx_sessions_user_id", "user_id"),
    )

    def __repr__(self):
        return f"<Session(id={self.id}, user_id={self.user_id}, device='{self.device_name}')>"


class Chat(Base):
    """Таблица чатов (личные, группы, каналы)"""
    __tablename__ = "chats"

    id = Column(GUID(), primary_key=True, default=uuid4)
    chat_type = Column(SQLEnum(ChatType), nullable=False)
    name = Column(String(255))
    description = Column(Text)
    avatar_url = Column(Text)
    owner_id = Column(GUID(), ForeignKey("users.id"))
    max_participants = Column(Integer, default=200)
    is_read_only = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="owned_chats", foreign_keys=[owner_id])
    members = relationship("ChatMember", back_populates="chat", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_chats_type", "chat_type"),
    )

    def __repr__(self):
        return f"<Chat(id={self.id}, type='{self.chat_type}', name='{self.name}')>"


class ChatMember(Base):
    """Участники чатов"""
    __tablename__ = "chat_members"

    id = Column(GUID(), primary_key=True, default=uuid4)
    chat_id = Column(GUID(), ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(SQLEnum(MemberRole), default=MemberRole.MEMBER)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    chat = relationship("Chat", back_populates="members")
    user = relationship("User", back_populates="memberships")

    __table_args__ = (
        UniqueConstraint("chat_id", "user_id", name="uq_chat_member"),
        Index("idx_chat_members_user_id", "user_id"),
    )

    def __repr__(self):
        return f"<ChatMember(chat_id={self.chat_id}, user_id={self.user_id}, role='{self.role}')>"


class Message(Base):
    """Таблица сообщений"""
    __tablename__ = "messages"

    id = Column(GUID(), primary_key=True, default=uuid4)
    chat_id = Column(GUID(), ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(GUID(), ForeignKey("users.id"))
    content = Column(Text)
    message_type = Column(SQLEnum(MessageType), default=MessageType.TEXT)
    reply_to_id = Column(GUID(), ForeignKey("messages.id"))
    forwarded_from_id = Column(GUID(), ForeignKey("messages.id"))
    edited_at = Column(DateTime(timezone=True))
    deleted_at = Column(DateTime(timezone=True))
    is_pinned = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Для полнотекстового поиска (PostgreSQL)
    search_vector = Column(SEARCH_VECTOR())

    # Relationships
    chat = relationship("Chat", back_populates="messages")
    sender = relationship("User", back_populates="sent_messages", foreign_keys=[sender_id])
    reply_to = relationship("Message", remote_side=[id], foreign_keys=[reply_to_id])
    forwarded_from = relationship("Message", remote_side=[id], foreign_keys=[forwarded_from_id])
    media = relationship("Media", back_populates="message", cascade="all, delete-orphan")
    reactions = relationship("Reaction", back_populates="message", cascade="all, delete-orphan")
    read_receipts = relationship("ReadReceipt", back_populates="message", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_messages_created_at", "created_at"),
        Index("idx_messages_sender_id", "sender_id"),
        Index("idx_messages_search", "search_vector", postgresql_using="gin"),
    )

    def __repr__(self):
        return f"<Message(id={self.id}, chat_id={self.chat_id}, type='{self.message_type}')>"


class Reaction(Base):
    """Реакции на сообщения"""
    __tablename__ = "reactions"

    id = Column(GUID(), primary_key=True, default=uuid4)
    message_id = Column(GUID(), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    emoji = Column(String(10), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    message = relationship("Message", back_populates="reactions")
    user = relationship("User", back_populates="reactions")

    __table_args__ = (
        UniqueConstraint("message_id", "user_id", name="uq_reaction_user_message"),
    )

    def __repr__(self):
        return f"<Reaction(message_id={self.message_id}, user_id={self.user_id}, emoji='{self.emoji}')>"


class Media(Base):
    """Медиафайлы"""
    __tablename__ = "media"

    id = Column(GUID(), primary_key=True, default=uuid4)
    message_id = Column(GUID(), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(Text, nullable=False)
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100))
    thumbnail_path = Column(Text)
    width = Column(Integer)
    height = Column(Integer)
    duration = Column(Integer)  # в секундах для аудио/видео
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    message = relationship("Message", back_populates="media")

    def __repr__(self):
        return f"<Media(id={self.id}, size={self.file_size}, type='{self.mime_type}')>"


class SecretChat(Base):
    """Секретные чаты с end-to-end шифрованием"""
    __tablename__ = "secret_chats"

    id = Column(GUID(), primary_key=True, default=uuid4)
    user1_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    user2_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    encryption_key_hash = Column(String(255))
    self_destruct_timer = Column(Integer)  # в секундах
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user1_id", "user2_id", name="uq_secret_chat_users"),
    )

    def __repr__(self):
        return f"<SecretChat(id={self.id}, users={self.user1_id}-{self.user2_id})>"


class ReadReceipt(Base):
    """Статусы прочтения сообщений"""
    __tablename__ = "read_receipts"

    id = Column(GUID(), primary_key=True, default=uuid4)
    message_id = Column(GUID(), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    read_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    message = relationship("Message", back_populates="read_receipts")
    user = relationship("User", back_populates="read_receipts")

    __table_args__ = (
        UniqueConstraint("message_id", "user_id", name="uq_read_receipt"),
        Index("idx_read_receipts_user_id", "user_id"),
    )

    def __repr__(self):
        return f"<ReadReceipt(message_id={self.message_id}, user_id={self.user_id})>"
