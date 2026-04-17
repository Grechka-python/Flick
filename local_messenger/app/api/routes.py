"""
REST API маршруты для локального мессенджера.
"""

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.db.session import get_db
from app.schemas import (
    UserRegister, UserLogin, TokenResponse, UserResponse,
    ChatCreate, ChatResponse, MessageCreate, MessageResponse,
    SessionInfo, ChatMemberResponse, ReactionCreate,
)
from app.services.user_service import UserService, SessionService
from app.services.chat_service import ChatService, MessageService
from app.core.security import (
    get_password_hash, verify_password, create_access_token,
    create_refresh_token, decode_token, generate_totp_secret,
    verify_totp_code, hash_token,
)
from app.core.config import settings


# === Router Setup ===

router = APIRouter()


# === Helper Functions ===

async def get_current_user_id(
    token: str = None,
    db: AsyncSession = Depends(get_db),
) -> UUID:
    """Получение ID текущего пользователя из токена"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    return UUID(user_id)


# === Auth Routes ===

@router.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db),
):
    """Регистрация нового пользователя"""
    user_service = UserService(db)

    # Проверка существования пользователя
    existing = await user_service.get_by_username(user_data.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Создание пользователя
    user = await user_service.create(
        username=user_data.username,
        password=user_data.password,
        email=user_data.email,
        phone=user_data.phone,
    )

    return user


@router.post("/auth/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    """Вход в систему"""
    user_service = UserService(db)
    session_service = SessionService(db)

    # Поиск пользователя
    user = await user_service.get_by_username(credentials.username)
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    # Проверка 2FA если включена
    if user.totp_secret and credentials.totp_code:
        if not verify_totp_code(user.totp_secret, credentials.totp_code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid TOTP code",
            )
    elif user.totp_secret and not credentials.totp_code:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="TOTP code required",
            headers={"X-TOTP-Required": "true"},
        )

    # Создание токенов
    access_token = create_access_token(data={"sub": str(user.id), "username": user.username})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    # Хеширование токенов для хранения
    access_token_hash = hash_token(access_token)
    refresh_token_hash = hash_token(refresh_token)

    from datetime import datetime, timedelta
    expires_at = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # Создание сессии (упрощённо)
    # В реальном приложении нужно передавать device_info и ip_address
    session = await session_service.create(
        user_id=user.id,
        device_name="Unknown",
        device_type="web",
        ip_address="0.0.0.0",
        access_token_hash=access_token_hash,
        refresh_token_hash=refresh_token_hash,
        expires_at=expires_at,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.get("/auth/sessions", response_model=List[SessionInfo])
async def get_sessions(
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Получение списка активных сессий"""
    session_service = SessionService(db)
    sessions = await session_service.get_all_for_user(current_user_id)
    return sessions


@router.delete("/auth/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Удаление сессии"""
    session_service = SessionService(db)
    await session_service.deactivate(session_id)


# === User Routes ===

@router.get("/users/me", response_model=UserResponse)
async def get_current_user(
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Получение данных текущего пользователя"""
    user_service = UserService(db)
    user = await user_service.get_by_id(current_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/users/me", response_model=UserResponse)
async def update_current_user(
    email: str = None,
    phone: str = None,
    avatar_url: str = None,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Обновление данных текущего пользователя"""
    user_service = UserService(db)
    user = await user_service.update(
        user_id=current_user_id,
        email=email,
        phone=phone,
        avatar_url=avatar_url,
    )
    return user


@router.post("/users/search", response_model=List[UserResponse])
async def search_users(
    query: str,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """Поиск пользователей"""
    user_service = UserService(db)
    users = await user_service.search(query=query, limit=limit, offset=offset)
    return users


# === Chat Routes ===

@router.get("/chats", response_model=List[ChatResponse])
async def get_chats(
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Получение списка чатов пользователя"""
    chat_service = ChatService(db)
    chats = await chat_service.get_user_chats(current_user_id)
    return chats


@router.post("/chats", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(
    chat_data: ChatCreate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Создание нового чата/группы/канала"""
    chat_service = ChatService(db)

    chat = await chat_service.create(
        chat_type=chat_data.chat_type,
        owner_id=current_user_id,
        name=chat_data.name,
        description=chat_data.description,
        member_ids=chat_data.member_ids,
        max_participants=chat_data.max_participants,
        is_read_only=chat_data.is_read_only,
    )

    return chat


@router.get("/chats/{chat_id}", response_model=ChatResponse)
async def get_chat(
    chat_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Получение информации о чате"""
    chat_service = ChatService(db)
    chat = await chat_service.get_by_id(chat_id)

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Проверка доступа
    member = await chat_service.get_member(chat_id, current_user_id)
    if not member and chat.owner_id != current_user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return chat


@router.post("/chats/{chat_id}/members", response_model=ChatMemberResponse)
async def add_chat_member(
    chat_id: UUID,
    user_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Добавление участника в чат"""
    chat_service = ChatService(db)

    # Проверка доступа
    member = await chat_service.get_member(chat_id, current_user_id)
    if not member or member.role not in ['owner', 'admin']:
        raise HTTPException(status_code=403, detail="Access denied")

    new_member = await chat_service.add_member(chat_id, user_id)
    return new_member


@router.delete("/chats/{chat_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_chat_member(
    chat_id: UUID,
    user_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Удаление участника из чата"""
    chat_service = ChatService(db)

    # Проверка доступа
    member = await chat_service.get_member(chat_id, current_user_id)
    if not member or member.role not in ['owner', 'admin']:
        raise HTTPException(status_code=403, detail="Access denied")

    await chat_service.remove_member(chat_id, user_id)


# === Message Routes ===

@router.get("/chats/{chat_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    chat_id: UUID,
    limit: int = 50,
    offset: int = 0,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Получение истории сообщений чата"""
    chat_service = ChatService(db)
    message_service = MessageService(db)

    # Проверка доступа
    member = await chat_service.get_member(chat_id, current_user_id)
    if not member:
        raise HTTPException(status_code=403, detail="Access denied")

    messages = await message_service.get_chat_messages(
        chat_id=chat_id,
        limit=limit,
        offset=offset,
    )

    return messages


@router.post("/chats/{chat_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    chat_id: UUID,
    message_data: MessageCreate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Отправка сообщения"""
    chat_service = ChatService(db)
    message_service = MessageService(db)

    # Проверка доступа
    member = await chat_service.get_member(chat_id, current_user_id)
    if not member:
        raise HTTPException(status_code=403, detail="Access denied")

    message = await message_service.create(
        chat_id=chat_id,
        sender_id=current_user_id,
        content=message_data.content,
        message_type=message_data.message_type,
        reply_to_id=message_data.reply_to_id,
        forwarded_from_id=message_data.forwarded_from_id,
    )

    return message


@router.put("/messages/{message_id}", response_model=MessageResponse)
async def edit_message(
    message_id: UUID,
    content: str,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Редактирование сообщения"""
    message_service = MessageService(db)

    message = await message_service.get_by_id(message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    if message.sender_id != current_user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    updated_message = await message_service.update(message_id=message_id, content=content)
    return updated_message


@router.delete("/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Удаление сообщения"""
    message_service = MessageService(db)

    message = await message_service.get_by_id(message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    if message.sender_id != current_user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    await message_service.delete(message_id)


@router.post("/messages/{message_id}/reactions", status_code=status.HTTP_201_CREATED)
async def add_reaction(
    message_id: UUID,
    reaction_data: ReactionCreate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Добавление реакции к сообщению"""
    message_service = MessageService(db)

    reaction = await message_service.add_reaction(
        message_id=message_id,
        user_id=current_user_id,
        emoji=reaction_data.emoji,
    )

    return reaction


@router.post("/messages/{message_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_message_read(
    message_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Отметить сообщение как прочитанное"""
    message_service = MessageService(db)
    await message_service.mark_as_read(message_id=message_id, user_id=current_user_id)
