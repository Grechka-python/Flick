"""
Pydantic схемы для валидации данных API.
Используется для REST API и WebSocket сообщений.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Any
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr


# === Enums ===

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


# === Auth Schemas ===

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)


class UserLogin(BaseModel):
    username: str
    password: str
    totp_code: Optional[str] = Field(None, min_length=6, max_length=6)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefresh(BaseModel):
    refresh_token: str


class TOTPVerify(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)


# === User Schemas ===

class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None


class UserResponse(UserBase):
    id: UUID
    is_active: bool
    storage_quota: int
    created_at: datetime
    last_seen: Optional[datetime] = None

    class Config:
        from_attributes = True


class SessionInfo(BaseModel):
    id: UUID
    device_name: str
    device_type: DeviceType
    ip_address: str
    created_at: datetime
    last_activity: datetime
    expires_at: datetime

    class Config:
        from_attributes = True


# === Chat Schemas ===

class ChatCreate(BaseModel):
    chat_type: ChatType
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    member_ids: List[UUID] = []
    max_participants: Optional[int] = Field(200, ge=2)
    is_read_only: bool = False


class ChatUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    avatar_url: Optional[str] = None
    is_read_only: Optional[bool] = None


class ChatMemberAdd(BaseModel):
    user_id: UUID


class ChatMemberRoleUpdate(BaseModel):
    role: MemberRole


class ChatResponse(BaseModel):
    id: UUID
    chat_type: ChatType
    name: Optional[str] = None
    description: Optional[str] = None
    avatar_url: Optional[str] = None
    owner_id: UUID
    max_participants: int
    is_read_only: bool
    created_at: datetime
    updated_at: datetime
    member_count: int = 0
    last_message_preview: Optional[str] = None
    unread_count: int = 0

    class Config:
        from_attributes = True


class ChatMemberResponse(BaseModel):
    id: UUID
    user_id: UUID
    username: str
    avatar_url: Optional[str] = None
    role: MemberRole
    joined_at: datetime

    class Config:
        from_attributes = True


# === Message Schemas ===

class MessageCreate(BaseModel):
    content: Optional[str] = None
    message_type: MessageType = MessageType.TEXT
    reply_to_id: Optional[UUID] = None
    forwarded_from_id: Optional[UUID] = None
    media_ids: List[UUID] = []


class MessageUpdate(BaseModel):
    content: str


class ReactionCreate(BaseModel):
    emoji: str = Field(..., max_length=10)


class MessageResponse(BaseModel):
    id: UUID
    chat_id: UUID
    sender_id: UUID
    sender_username: str
    sender_avatar: Optional[str] = None
    content: Optional[str] = None
    message_type: MessageType
    reply_to: Optional["MessageResponse"] = None
    forwarded_from: Optional["MessageResponse"] = None
    media: List["MediaResponse"] = []
    reactions: List["ReactionResponse"] = []
    is_pinned: bool
    edited_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    created_at: datetime
    read_by: List[UUID] = []

    class Config:
        from_attributes = True


class ReactionResponse(BaseModel):
    id: UUID
    user_id: UUID
    username: str
    emoji: str
    created_at: datetime

    class Config:
        from_attributes = True


# === Media Schemas ===

class MediaUploadResponse(BaseModel):
    id: UUID
    file_path: str
    file_size: int
    mime_type: str
    thumbnail_path: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[int] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True


class MediaResponse(BaseModel):
    id: UUID
    file_path: str
    file_size: int
    mime_type: str
    thumbnail_path: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[int] = None

    class Config:
        from_attributes = True


# === Secret Chat Schemas ===

class SecretChatCreate(BaseModel):
    user_id: UUID
    self_destruct_timer: Optional[int] = Field(None, ge=5)  # секунды


class SecretChatResponse(BaseModel):
    id: UUID
    user1_id: UUID
    user2_id: UUID
    self_destruct_timer: Optional[int] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# === Search Schemas ===

class SearchMessagesRequest(BaseModel):
    query: str
    chat_id: Optional[UUID] = None
    sender_id: Optional[UUID] = None
    message_type: Optional[MessageType] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = Field(50, ge=1, le=100)
    offset: int = 0


class SearchResult(BaseModel):
    messages: List[MessageResponse]
    total: int


# === Admin Schemas ===

class AdminUserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    storage_quota: Optional[int] = None


class LogEntry(BaseModel):
    id: UUID
    user_id: UUID
    action: str
    target_type: str
    target_id: Optional[UUID] = None
    ip_address: str
    timestamp: datetime

    class Config:
        from_attributes = True


# === WebSocket Schemas ===

class WSMessageType(str, Enum):
    # Client to Server
    SEND_MESSAGE = "send_message"
    EDIT_MESSAGE = "edit_message"
    DELETE_MESSAGE = "delete_message"
    ADD_REACTION = "add_reaction"
    REMOVE_REACTION = "remove_reaction"
    MARK_READ = "mark_read"
    TYPING_START = "typing_start"
    TYPING_STOP = "typing_stop"
    CALL_START = "call_start"
    CALL_END = "call_end"
    SUBSCRIBE_CHAT = "subscribe_chat"
    UNSUBSCRIBE_CHAT = "unsubscribe_chat"

    # Server to Client
    NEW_MESSAGE = "new_message"
    MESSAGE_UPDATED = "message_updated"
    MESSAGE_DELETED = "message_deleted"
    USER_ONLINE = "user_online"
    USER_OFFLINE = "user_offline"
    TYPING_STATUS = "typing_status"
    READ_RECEIPT = "read_receipt"
    REACTION_ADDED = "reaction_added"
    REACTION_REMOVED = "reaction_removed"
    CHAT_UPDATED = "chat_updated"
    MEMBER_ADDED = "member_added"
    MEMBER_REMOVED = "member_removed"
    CALL_INCOMING = "call_incoming"
    CALL_ENDED = "call_ended"
    ERROR = "error"


class WSMessage(BaseModel):
    type: WSMessageType
    payload: Any
    request_id: Optional[str] = None


class WSTypingStatus(BaseModel):
    chat_id: UUID
    user_id: UUID
    is_typing: bool


class WSReadReceipt(BaseModel):
    message_id: UUID
    chat_id: UUID
    user_id: UUID
    read_at: datetime


class WSCallEvent(BaseModel):
    call_id: UUID
    chat_id: UUID
    caller_id: UUID
    callee_id: UUID
    call_type: str  # 'voice' or 'video'


class WSError(BaseModel):
    code: int
    message: str
    details: Optional[dict] = None


# Обновляем forward references
MessageResponse.update_forward_refs()
