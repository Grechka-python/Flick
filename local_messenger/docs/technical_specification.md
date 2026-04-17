# Техническое описание локального мессенджера (MVP)

## 1. Функциональные требования

### 1.1 Личные сообщения
- Отправка текста, эмодзи, реакций (лайк, сердечко и т.д.)
- Редактирование/удаление сообщений за последние 48 часов
- Ответы на конкретные сообщения (reply)
- Пересылка сообщений
- Цитирование

### 1.2 Медиафайлы
- Отправка изображений, видео, аудио, документов (любых форматов)
- Максимальный размер файла: 2 ГБ
- Сжатие изображений по желанию пользователя

### 1.3 Голосовые и видеозвонки
- End-to-end шифрование
- Переключение камеры/микрофона
- Адаптивное качество (до 4K при достаточной пропускной способности)

### 1.4 Группы (до 200 участников)
- Создание групп
- Приглашение по локальному ID/QR-коду
- Назначение администраторов
- Закреплённые сообщения
- Режим «только для чтения» для участников

### 1.5 Каналы (неограниченная аудитория)
- Односторонняя рассылка
- Подписка через локальный сервер
- Комментарии в отдельной группе

### 1.6 Облачное хранилище (локальное)
- Синхронизация истории между устройствами одного пользователя
- Лимит: 10 ГБ на пользователя (расширяется администратором)

### 1.7 Поиск
- По тексту (русский и английский языки)
- По датам
- По типу медиа
- По отправителю

### 1.8 Управление сессиями
- Список всех активных устройств
- Удаление любой сессии

### 1.9 Секретные чаты
- Device-to-device шифрование
- Отсутствие облачного бэкапа
- Таймер самоуничтожения: от 5 секунд до 1 недели

### 1.10 Боты
- API для создания локальных ботов
- Боты работают как отдельные аккаунты

### 1.11 Административные функции
- Создание/удаление пользователей через мастер-аккаунт
- Резервное копирование чатов
- Логирование метаданных (без доступа к содержимому)

---

## 2. Технические ограничения для локальной сети

### 2.1 Хранение данных
- Все данные только на локальном сервере
- Без облачных провайдеров

### 2.2 Аутентификация
- Логин/пароль
- Двухфакторная аутентификация (TOTP)
- Локальный сервер времени

### 2.3 Протокол связи
- TCP/WebSocket с TLS 1.3
- Для секретных чатов: Double Ratchet (аналог MTProto)

### 2.4 База данных
- PostgreSQL для метаданных
- MinIO для объектного хранилища файлов

### 2.5 Клиенты
- Платформы: Windows, Linux, macOS, Android, iOS
- Фреймворк: Flutter (кроссплатформенность) или Qt

---

## 3. Детальное описание GUI (сине-оранжевая стилистика)

### 3.1 Цветовая палитра
| Элемент | Цвет | HEX |
|---------|------|-----|
| Основной фон | Глубокий синий | #0A2F6C |
| Акцент | Яркий оранжевый | #FF8C42 |
| Боковая панель | Тёмно-синий | #0F2A4A |
| Пузырь отправителя | Тёмно-синий | #0E3B5C |
| Пузырь собеседника | Серо-синий | #1C2E40 |
| Градиент шапки | #0A2F6C → #1E4A7A | - |
| Текст | Белый / светло-серый | #FFFFFF / #CCCCCC |

### 3.2 Боковая панель (список чатов)
- Фон: #0F2A4A
- Непрочитанные сообщения: оранжевая полоса слева (#FF8C42)
- Аватарки: круглые, оранжевый ободок для активных пользователей
- Имя чата: белый текст
- Последнее сообщение: светло-серый текст

### 3.3 Шапка чата
- Фон: градиент от #0A2F6C до #1E4A7A
- Кнопка назад: белая иконка, при наведении — оранжевая
- Имя собеседника: оранжевый цвет (#FF8C42)
- Иконка вызова: оранжевая
- Иконка поиска: белая, при наведении — оранжевая

### 3.4 Область сообщений
- Пузыри отправителя: #0E3B5C, белый текст
- Пузыри собеседника: #1C2E40, белый текст
- Галочки прочтения: оранжевые (одинарная — отправлено, двойная — прочитано)
- Кнопка отправки файла: оранжевая скрепка
- Поле ввода: тёмно-синее, белый текст, оранжевый курсор
- Кнопка отправки: оранжевая

### 3.5 Модальные окна
- Фон: синий (#0A2F6C)
- Кнопка «Подтвердить»: оранжевая (#FF8C42)
- Кнопка «Отмена»: белая с прозрачностью 50%

### 3.6 Уведомления (тосты)
- Фон: чёрный полупрозрачный (rgba(0,0,0,0.8))
- Заголовок: оранжевый
- Текст: белый

### 3.7 Иконки
- Системные иконки (микрофон, камера, скрепка, звонок, настройки): белые
- При наведении/активном состоянии: оранжевые

---

## 4. Схема базы данных

```sql
-- Таблица пользователей
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(20),
    avatar_url TEXT,
    status VARCHAR(20) DEFAULT 'offline',
    last_seen TIMESTAMP,
    storage_used BIGINT DEFAULT 0,
    storage_limit BIGINT DEFAULT 10737418240, -- 10 GB
    is_admin BOOLEAN DEFAULT FALSE,
    is_bot BOOLEAN DEFAULT FALSE,
    bot_token VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Двухфакторная аутентификация
CREATE TABLE user_2fa (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    totp_secret VARCHAR(32) NOT NULL,
    backup_codes TEXT[],
    enabled BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (user_id)
);

-- Таблица чатов (личные, группы, каналы)
CREATE TABLE chats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(20) NOT NULL, -- 'private', 'group', 'channel'
    name VARCHAR(100),
    description TEXT,
    avatar_url TEXT,
    owner_id UUID REFERENCES users(id),
    is_read_only BOOLEAN DEFAULT FALSE,
    max_members INTEGER DEFAULT 200,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Участники чатов
CREATE TABLE chat_members (
    chat_id UUID REFERENCES chats(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) DEFAULT 'member', -- 'owner', 'admin', 'member'
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (chat_id, user_id)
);

-- Сообщения
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id UUID REFERENCES chats(id) ON DELETE CASCADE,
    sender_id UUID REFERENCES users(id),
    content TEXT,
    reply_to_message_id UUID REFERENCES messages(id),
    forwarded_from_id UUID REFERENCES messages(id),
    edited_at TIMESTAMP,
    deleted_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP -- для секретных чатов
);

-- Реакции на сообщения
CREATE TABLE message_reactions (
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    reaction_type VARCHAR(20) NOT NULL, -- 'like', 'heart', 'laugh', etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (message_id, user_id)
);

-- Медиафайлы
CREATE TABLE media (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    file_type VARCHAR(20) NOT NULL, -- 'image', 'video', 'audio', 'document'
    file_name VARCHAR(255) NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100),
    storage_path TEXT NOT NULL, -- путь в MinIO
    thumbnail_path TEXT,
    width INTEGER,
    height INTEGER,
    duration INTEGER, -- для аудио/видео в секундах
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Сессии пользователей
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    device_type VARCHAR(20), -- 'desktop', 'mobile', 'web'
    device_name VARCHAR(100),
    ip_address INET,
    user_agent TEXT,
    refresh_token VARCHAR(255) NOT NULL,
    access_token VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Секретные чаты (device-to-device)
CREATE TABLE secret_chats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user1_id UUID REFERENCES users(id),
    user2_id UUID REFERENCES users(id),
    encryption_key TEXT NOT NULL,
    self_destruct_timer INTEGER DEFAULT 0, -- в секундах, 0 = отключено
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user1_id, user2_id)
);

-- Сообщения секретных чатов
CREATE TABLE secret_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    secret_chat_id UUID REFERENCES secret_chats(id) ON DELETE CASCADE,
    sender_id UUID REFERENCES users(id),
    encrypted_content TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);

-- Закреплённые сообщения
CREATE TABLE pinned_messages (
    chat_id UUID REFERENCES chats(id) ON DELETE CASCADE,
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    pinned_by UUID REFERENCES users(id),
    pinned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (chat_id, message_id)
);

-- Индекс для полнотекстового поиска
ALTER TABLE messages ADD COLUMN search_vector tsvector;
CREATE INDEX messages_search_idx ON messages USING GIN(search_vector);

-- Триггер для обновления search_vector
CREATE OR REPLACE FUNCTION update_search_vector() RETURNS trigger AS $$
BEGIN
    NEW.search_vector := to_tsvector('russian', COALESCE(NEW.content, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER messages_search_update
    BEFORE INSERT OR UPDATE ON messages
    FOR EACH ROW
    EXECUTE FUNCTION update_search_vector();

-- Логирование метаданных
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    action VARCHAR(50) NOT NULL,
    target_type VARCHAR(50),
    target_id UUID,
    ip_address INET,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 5. API-эндпоинты

### 5.1 REST API

#### Аутентификация
```
POST   /api/v1/auth/register          # Регистрация нового пользователя
POST   /api/v1/auth/login             # Вход (логин/пароль)
POST   /api/v1/auth/logout            # Выход
POST   /api/v1/auth/refresh           # Обновление токена
POST   /api/v1/auth/2fa/enable        # Включение 2FA
POST   /api/v1/auth/2fa/verify        # Проверка 2FA кода
POST   /api/v1/auth/2fa/disable       # Отключение 2FA
```

#### Пользователи
```
GET    /api/v1/users/me               # Получение информации о текущем пользователе
PUT    /api/v1/users/me               # Обновление профиля
GET    /api/v1/users/:id              # Получение информации о пользователе
GET    /api/v1/users/search           # Поиск пользователей
DELETE /api/v1/users/:id              # Удаление пользователя (админ)
```

#### Чаты
```
GET    /api/v1/chats                  # Список всех чатов
POST   /api/v1/chats                  # Создание чата/группы/канала
GET    /api/v1/chats/:id              # Информация о чате
PUT    /api/v1/chats/:id              # Обновление чата
DELETE /api/v1/chats/:id              # Удаление чата
POST   /api/v1/chats/:id/members      # Добавить участника
DELETE /api/v1/chats/:id/members/:userId  # Удалить участника
PUT    /api/v1/chats/:id/members/:userId/role  # Изменить роль
```

#### Сообщения
```
GET    /api/v1/chats/:chatId/messages         # Получить сообщения (пагинация)
POST   /api/v1/chats/:chatId/messages         # Отправить сообщение
PUT    /api/v1/chats/:chatId/messages/:id     # Редактировать сообщение
DELETE /api/v1/chats/:chatId/messages/:id     # Удалить сообщение
POST   /api/v1/chats/:chatId/messages/:id/reply  # Ответить на сообщение
POST   /api/v1/chats/:chatId/messages/:id/forward  # Переслать сообщение
```

#### Реакции
```
POST   /api/v1/messages/:id/reactions   # Добавить реакцию
DELETE /api/v1/messages/:id/reactions   # Удалить реакцию
GET    /api/v1/messages/:id/reactions   # Получить все реакции
```

#### Медиафайлы
```
POST   /api/v1/upload                   # Загрузить файл (multipart/form-data)
GET    /api/v1/files/:id                # Получить информацию о файле
GET    /api/v1/files/:id/download       # Скачать файл
DELETE /api/v1/files/:id                # Удалить файл
```

#### Поиск
```
GET    /api/v1/search                   # Поиск по сообщениям
       Параметры: q, chat_id, from_date, to_date, type, sender_id
```

#### Сессии
```
GET    /api/v1/sessions                 # Список активных сессий
DELETE /api/v1/sessions/:id             # Завершить сессию
DELETE /api/v1/sessions/all             # Завершить все сессии
```

#### Секретные чаты
```
POST   /api/v1/secret-chats             # Создать секретный чат
GET    /api/v1/secret-chats             # Список секретных чатов
DELETE /api/v1/secret-chats/:id         # Удалить секретный чат
PUT    /api/v1/secret-chats/:id/timer   # Установить таймер самоуничтожения
```

#### Администрирование
```
GET    /api/v1/admin/users              # Список всех пользователей (админ)
POST   /api/v1/admin/users              # Создать пользователя (админ)
GET    /api/v1/admin/logs               # Получить логи аудита (админ)
POST   /api/v1/admin/backup             # Создать резервную копию (админ)
GET    /api/v1/admin/stats              # Статистика системы (админ)
```

### 5.2 WebSocket эндпоинты

```
ws://server/ws                         # Основное WebSocket соединение

События клиента → сервер:
- send_message {chat_id, content, reply_to, attachments}
- edit_message {message_id, new_content}
- delete_message {message_id}
- add_reaction {message_id, reaction_type}
- remove_reaction {message_id, reaction_type}
- typing_status {chat_id, is_typing}
- call_start {chat_id, type: 'voice'|'video'}
- call_accept {call_id}
- call_end {call_id}
- secret_message {secret_chat_id, encrypted_content}

События сервер → клиент:
- new_message {message object}
- message_updated {message_id, new_content, edited_at}
- message_deleted {message_id}
- reaction_added {message_id, user_id, reaction_type}
- reaction_removed {message_id, user_id}
- user_online {user_id}
- user_offline {user_id}
- typing_indicator {chat_id, user_id, is_typing}
- call_incoming {call_id, from_user, type}
- call_accepted {call_id}
- call_ended {call_id}
- secret_message_received {secret_chat_id, encrypted_content}
- session_terminated {session_id}
```

---

## 6. Блок-схема алгоритма отправки сообщения

```
┌─────────────┐
│   Клиент А  │
│  (Отправитель) │
└──────┬──────┘
       │
       │ 1. Пользователь вводит сообщение
       │    и нажимает "Отправить"
       ▼
┌─────────────────────────────────┐
│  Клиентская валидация:          │
│  - Проверка размера текста      │
│  - Проверка прикрепленных файлов│
│  - Шифрование (для секретных    │
│    чатов)                       │
└──────────────┬──────────────────┘
               │
               │ 2. POST /api/v1/chats/:chatId/messages
               │    или WebSocket: send_message
               ▼
       ┌───────────────┐
       │  Load Balancer│
       │  (опционально)│
       └───────┬───────┘
               │
               ▼
       ┌───────────────────┐
       │   Сервер приложений│
       │   (Go/Python)     │
       └─────────┬─────────┘
                 │
                 │ 3. Проверка аутентификации
                 │    и авторизации
                 ▼
       ┌───────────────────┐
       │  Валидация запроса│
       │  - Существует ли  │
       │    чат?           │
       │  - Есть ли доступ?│
       │  - Не превышен    │
       │    лимит?         │
       └─────────┬─────────┘
                 │
                 │ 4. Сохранение в БД
                 ▼
       ┌───────────────────┐
       │   PostgreSQL      │
       │   - INSERT INTO   │
       │     messages      │
       │   - Обновление    │
       │     search_vector │
       └─────────┬─────────┘
                 │
                 │ 5. Если есть медиафайлы
                 ▼
       ┌───────────────────┐
       │   MinIO           │
       │   - Загрузка файлов│
       │   - Генерация     │
       │     thumbnail     │
       └─────────┬─────────┘
                 │
                 │ 6. Уведомление получателей
                 ▼
       ┌───────────────────┐
       │   WebSocket Hub   │
       │   - Рассылка      │
       │     new_message   │
       │     всем участникам│
       │     чата          │
       └─────────┬─────────┘
                 │
                 │ 7. WebSocket: new_message
                 ▼
       ┌───────────────┐
       │   Клиент Б    │
       │  (Получатель) │
       └───────┬───────┘
               │
               │ 8. Отображение сообщения
               │    в интерфейсе
               ▼
       ┌───────────────────┐
       │  Локальная БД     │
       │  (кэширование)    │
       └───────────────────┘
```

---

## 7. Листинг ключевых структур данных

### 7.1 Структуры на Go (с горутинами)

```go
package models

import (
    "time"
    "github.com/google/uuid"
)

// User представляет пользователя системы
type User struct {
    ID           uuid.UUID  `json:"id" gorm:"type:uuid;primary_key"`
    Username     string     `json:"username" gorm:"uniqueIndex;size:50"`
    PasswordHash string     `json:"-" gorm:"size:255"`
    Email        *string    `json:"email,omitempty" gorm:"size:100"`
    Phone        *string    `json:"phone,omitempty" gorm:"size:20"`
    AvatarURL    *string    `json:"avatar_url,omitempty"`
    Status       string     `json:"status" gorm:"default:'offline'"`
    LastSeen     *time.Time `json:"last_seen,omitempty"`
    StorageUsed  int64      `json:"storage_used" gorm:"default:0"`
    StorageLimit int64      `json:"storage_limit" gorm:"default:10737418240"`
    IsAdmin      bool       `json:"is_admin" gorm:"default:false"`
    IsBot        bool       `json:"is_bot" gorm:"default:false"`
    BotToken     *string    `json:"bot_token,omitempty"`
    CreatedAt    time.Time  `json:"created_at"`
    UpdatedAt    time.Time  `json:"updated_at"`
}

// ChatType определяет тип чата
type ChatType string

const (
    ChatTypePrivate ChatType = "private"
    ChatTypeGroup   ChatType = "group"
    ChatTypeChannel ChatType = "channel"
)

// Chat представляет чат (личный, группу или канал)
type Chat struct {
    ID          uuid.UUID  `json:"id" gorm:"type:uuid;primary_key"`
    Type        ChatType   `json:"type"`
    Name        *string    `json:"name,omitempty" gorm:"size:100"`
    Description *string    `json:"description,omitempty"`
    AvatarURL   *string    `json:"avatar_url,omitempty"`
    OwnerID     *uuid.UUID `json:"owner_id,omitempty" gorm:"type:uuid"`
    Owner       *User      `json:"owner,omitempty" gorm:"foreignKey:OwnerID"`
    IsReadOnly  bool       `json:"is_read_only" gorm:"default:false"`
    MaxMembers  int        `json:"max_members" gorm:"default:200"`
    Members     []ChatMember `json:"members,omitempty" gorm:"foreignKey:ChatID"`
    Messages    []Message  `json:"messages,omitempty" gorm:"foreignKey:ChatID"`
    CreatedAt   time.Time  `json:"created_at"`
    UpdatedAt   time.Time  `json:"updated_at"`
}

// MemberRole определяет роль участника
type MemberRole string

const (
    RoleOwner  MemberRole = "owner"
    RoleAdmin  MemberRole = "admin"
    RoleMember MemberRole = "member"
)

// ChatMember представляет участника чата
type ChatMember struct {
    ChatID    uuid.UUID `json:"chat_id" gorm:"type:uuid;primary_key"`
    UserID    uuid.UUID `json:"user_id" gorm:"type:uuid;primary_key"`
    Role      MemberRole `json:"role" gorm:"default:'member'"`
    JoinedAt  time.Time `json:"joined_at"`
    Chat      *Chat     `json:"chat,omitempty" gorm:"foreignKey:ChatID"`
    User      *User     `json:"user,omitempty" gorm:"foreignKey:UserID"`
}

// MessageType определяет тип контента сообщения
type MessageType string

const (
    MessageTypeText      MessageType = "text"
    MessageTypeImage     MessageType = "image"
    MessageTypeVideo     MessageType = "video"
    MessageTypeAudio     MessageType = "audio"
    MessageTypeDocument  MessageType = "document"
    MessageTypeVoice     MessageType = "voice"
)

// Message представляет сообщение в чате
type Message struct {
    ID                 uuid.UUID      `json:"id" gorm:"type:uuid;primary_key"`
    ChatID             uuid.UUID      `json:"chat_id" gorm:"type:uuid;index"`
    Chat               *Chat          `json:"chat,omitempty" gorm:"foreignKey:ChatID"`
    SenderID           uuid.UUID      `json:"sender_id" gorm:"type:uuid;index"`
    Sender             *User          `json:"sender,omitempty" gorm:"foreignKey:SenderID"`
    Content            string         `json:"content"`
    MessageType        MessageType    `json:"message_type" gorm:"default:'text'"`
    ReplyToMessageID   *uuid.UUID     `json:"reply_to_message_id,omitempty" gorm:"type:uuid"`
    ReplyToMessage     *Message       `json:"reply_to_message,omitempty" gorm:"foreignKey:ReplyToMessageID"`
    ForwardedFromID    *uuid.UUID     `json:"forwarded_from_id,omitempty" gorm:"type:uuid"`
    EditedAt           *time.Time     `json:"edited_at,omitempty"`
    DeletedAt          *time.Time     `json:"deleted_at,omitempty"`
    IsDeleted          bool           `json:"is_deleted" gorm:"default:false"`
    ExpiresAt          *time.Time     `json:"expires_at,omitempty"` // для секретных чатов
    Media              []Media        `json:"media,omitempty" gorm:"foreignKey:MessageID"`
    Reactions          []MessageReaction `json:"reactions,omitempty" gorm:"foreignKey:MessageID"`
    SearchVector       string         `json:"-" gorm:"type:tsvector"`
    CreatedAt          time.Time      `json:"created_at"`
}

// ReactionType определяет тип реакции
type ReactionType string

const (
    ReactionLike    ReactionType = "like"
    ReactionHeart   ReactionType = "heart"
    ReactionLaugh   ReactionType = "laugh"
    ReactionWow     ReactionType = "wow"
    ReactionSad     ReactionType = "sad"
    ReactionAngry   ReactionType = "angry"
)

// MessageReaction представляет реакцию на сообщение
type MessageReaction struct {
    MessageID    uuid.UUID    `json:"message_id" gorm:"type:uuid;primary_key"`
    UserID       uuid.UUID    `json:"user_id" gorm:"type:uuid;primary_key"`
    ReactionType ReactionType `json:"reaction_type"`
    CreatedAt    time.Time    `json:"created_at"`
    Message      *Message     `json:"message,omitempty" gorm:"foreignKey:MessageID"`
    User         *User        `json:"user,omitempty" gorm:"foreignKey:UserID"`
}

// FileType определяет тип файла
type FileType string

const (
    FileTypeImage    FileType = "image"
    FileTypeVideo    FileType = "video"
    FileTypeAudio    FileType = "audio"
    FileTypeDocument FileType = "document"
)

// Media представляет медиафайл
type Media struct {
    ID            uuid.UUID `json:"id" gorm:"type:uuid;primary_key"`
    MessageID     uuid.UUID `json:"message_id" gorm:"type:uuid;index"`
    Message       *Message  `json:"message,omitempty" gorm:"foreignKey:MessageID"`
    FileType      FileType  `json:"file_type"`
    FileName      string    `json:"file_name" gorm:"size:255"`
    FileSize      int64     `json:"file_size"`
    MimeType      string    `json:"mime_type" gorm:"size:100"`
    StoragePath   string    `json:"storage_path"` // путь в MinIO
    ThumbnailPath *string   `json:"thumbnail_path,omitempty"`
    Width         *int      `json:"width,omitempty"`
    Height        *int      `json:"height,omitempty"`
    Duration      *int      `json:"duration,omitempty"` // секунды
    UploadedAt    time.Time `json:"uploaded_at"`
}

// Session представляет активную сессию пользователя
type Session struct {
    ID           uuid.UUID  `json:"id" gorm:"type:uuid;primary_key"`
    UserID       uuid.UUID  `json:"user_id" gorm:"type:uuid;index"`
    User         *User      `json:"user,omitempty" gorm:"foreignKey:UserID"`
    DeviceType   string     `json:"device_type" gorm:"size:20"` // desktop, mobile, web
    DeviceName   *string    `json:"device_name,omitempty" gorm:"size:100"`
    IPAddress    string     `json:"ip_address" gorm:"type:inet"`
    UserAgent    *string    `json:"user_agent,omitempty"`
    RefreshToken string     `json:"-" gorm:"size:255"`
    AccessToken  string     `json:"-" gorm:"size:255"`
    ExpiresAt    time.Time  `json:"expires_at"`
    LastActive   time.Time  `json:"last_active"`
    IsActive     bool       `json:"is_active" gorm:"default:true"`
    CreatedAt    time.Time  `json:"created_at"`
}

// SecretChat представляет секретный чат с E2EE
type SecretChat struct {
    ID                 uuid.UUID `json:"id" gorm:"type:uuid;primary_key"`
    User1ID            uuid.UUID `json:"user1_id" gorm:"type:uuid;index"`
    User2ID            uuid.UUID `json:"user2_id" gorm:"type:uuid;index"`
    EncryptionKey      string    `json:"-"` // никогда не сохраняется в БД в продакшене
    SelfDestructTimer  int       `json:"self_destruct_timer" gorm:"default:0"` // секунды
    IsActive           bool      `json:"is_active" gorm:"default:true"`
    CreatedAt          time.Time `json:"created_at"`
}

// SecretMessage представляет сообщение в секретном чате
type SecretMessage struct {
    ID            uuid.UUID `json:"id" gorm:"type:uuid;primary_key"`
    SecretChatID  uuid.UUID `json:"secret_chat_id" gorm:"type:uuid;index"`
    SenderID      uuid.UUID `json:"sender_id" gorm:"type:uuid"`
    EncryptedContent string `json:"encrypted_content"`
    IsRead        bool      `json:"is_read" gorm:"default:false"`
    CreatedAt     time.Time `json:"created_at"`
    ExpiresAt     time.Time `json:"expires_at"`
}

// AuditLog представляет запись аудита
type AuditLog struct {
    ID         int64      `json:"id" gorm:"primary_key"`
    UserID     *uuid.UUID `json:"user_id,omitempty" gorm:"type:uuid"`
    Action     string     `json:"action" gorm:"size:50"`
    TargetType *string    `json:"target_type,omitempty" gorm:"size:50"`
    TargetID   *uuid.UUID `json:"target_id,omitempty" gorm:"type:uuid"`
    IPAddress  *string    `json:"ip_address,omitempty" gorm:"type:inet"`
    Timestamp  time.Time  `json:"timestamp" gorm:"default:CURRENT_TIMESTAMP"`
}
```

### 7.2 Структуры на Python (с asyncio)

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID
import asyncio


class ChatType(str, Enum):
    PRIVATE = "private"
    GROUP = "group"
    CHANNEL = "channel"


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
    VOICE = "voice"


class ReactionType(str, Enum):
    LIKE = "like"
    HEART = "heart"
    LAUGH = "laugh"
    WOW = "wow"
    SAD = "sad"
    ANGRY = "angry"


class FileType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"


@dataclass
class User:
    id: UUID
    username: str
    password_hash: str
    email: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    status: str = "offline"
    last_seen: Optional[datetime] = None
    storage_used: int = 0
    storage_limit: int = 10737418240  # 10 GB
    is_admin: bool = False
    is_bot: bool = False
    bot_token: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Chat:
    id: UUID
    type: ChatType
    name: Optional[str] = None
    description: Optional[str] = None
    avatar_url: Optional[str] = None
    owner_id: Optional[UUID] = None
    is_read_only: bool = False
    max_members: int = 200
    members: List['ChatMember'] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ChatMember:
    chat_id: UUID
    user_id: UUID
    role: MemberRole = MemberRole.MEMBER
    joined_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Media:
    id: UUID
    message_id: UUID
    file_type: FileType
    file_name: str
    file_size: int
    mime_type: str
    storage_path: str
    thumbnail_path: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[int] = None
    uploaded_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Message:
    id: UUID
    chat_id: UUID
    sender_id: UUID
    content: str
    message_type: MessageType = MessageType.TEXT
    reply_to_message_id: Optional[UUID] = None
    forwarded_from_id: Optional[UUID] = None
    edited_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    is_deleted: bool = False
    expires_at: Optional[datetime] = None
    media: List[Media] = field(default_factory=list)
    reactions: List['MessageReaction'] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MessageReaction:
    message_id: UUID
    user_id: UUID
    reaction_type: ReactionType
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Session:
    id: UUID
    user_id: UUID
    device_type: str
    device_name: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    refresh_token: str = ""
    access_token: str = ""
    expires_at: datetime = field(default_factory=datetime.utcnow)
    last_active: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SecretChat:
    id: UUID
    user1_id: UUID
    user2_id: UUID
    encryption_key: str
    self_destruct_timer: int = 0
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SecretMessage:
    id: UUID
    secret_chat_id: UUID
    sender_id: UUID
    encrypted_content: str
    is_read: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AuditLog:
    id: int
    user_id: Optional[UUID]
    action: str
    target_type: Optional[str]
    target_id: Optional[UUID]
    ip_address: Optional[str]
    timestamp: datetime = field(default_factory=datetime.utcnow)


# WebSocket Message Handler (asyncio)
class WebSocketMessageHandler:
    def __init__(self):
        self.connections: dict[UUID, asyncio.Queue] = {}
        self.lock = asyncio.Lock()
    
    async def register(self, user_id: UUID, queue: asyncio.Queue):
        async with self.lock:
            self.connections[user_id] = queue
    
    async def unregister(self, user_id: UUID):
        async with self.lock:
            if user_id in self.connections:
                del self.connections[user_id]
    
    async def broadcast_to_chat(self, chat_id: UUID, message: dict):
        """Отправить сообщение всем участникам чата"""
        async with self.lock:
            for user_id, queue in self.connections.items():
                # Здесь должна быть логика проверки участия в чате
                try:
                    await queue.put(message)
                except asyncio.QueueFull:
                    pass
    
    async def send_to_user(self, user_id: UUID, message: dict):
        """Отправить сообщение конкретному пользователю"""
        async with self.lock:
            if user_id in self.connections:
                try:
                    await self.connections[user_id].put(message)
                except asyncio.QueueFull:
                    pass


# Пример использования асинхронной обработки сообщений
async def process_message(
    message: Message,
    db_session,
    websocket_handler: WebSocketMessageHandler
):
    """Асинхронная обработка и отправка сообщения"""
    
    # 1. Сохранение в БД
    await db_session.execute(
        insert(MessageTable),
        values=message.__dict__
    )
    await db_session.commit()
    
    # 2. Обработка медиафайлов
    if message.media:
        for media_item in message.media:
            await upload_to_minio(media_item)
    
    # 3. Отправка через WebSocket
    ws_message = {
        "type": "new_message",
        "data": {
            "id": str(message.id),
            "chat_id": str(message.chat_id),
            "sender_id": str(message.sender_id),
            "content": message.content,
            "created_at": message.created_at.isoformat()
        }
    }
    
    await websocket_handler.broadcast_to_chat(
        message.chat_id,
        ws_message
    )
    
    # 4. Обновление статуса "печатает"
    await websocket_handler.send_to_user(
        message.sender_id,
        {"type": "typing_status", "data": {"is_typing": False}}
    )
```

---

## 8. Архитектурные компоненты

### 8.1 Серверная архитектура

```
┌─────────────────────────────────────────────────────────┐
│                    Клиенты (Flutter)                     │
│  Windows │ Linux │ macOS │ Android │ iOS │ Web          │
└─────────────────────────────────────────────────────────┘
                          │
                          │ TLS 1.3
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   Nginx / HAProxy                        │
│              (Load Balancer + Reverse Proxy)             │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              Сервер приложений (Go/Python)               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ REST API     │  │ WebSocket    │  │ Auth Service │  │
│  │ Handlers     │  │ Hub          │  │ (JWT + TOTP) │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Message      │  │ Media        │  │ Secret Chat  │  │
│  │ Processor    │  │ Processor    │  │ E2EE         │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  PostgreSQL  │ │    MinIO     │ │    Redis     │
│  (Metadata)  │ │   (Files)    │ │   (Cache &   │
│              │ │              │ │    Sessions) │
└──────────────┘ └──────────────┘ └──────────────┘
```

### 8.2 Компоненты безопасности

1. **TLS 1.3** - шифрование всего трафика
2. **JWT токены** - аутентификация с коротким временем жизни
3. **TOTP (RFC 6238)** - двухфакторная аутентификация
4. **Double Ratchet** - для секретных чатов
5. **Argon2** - хеширование паролей
6. **Rate limiting** - защита от брутфорса

---

## 9. Развёртывание (Docker Compose)

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: messenger
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: messenger
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - messenger_net

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_PASSWORD}
    volumes:
      - minio_data:/data
    ports:
      - "9000:9000"
      - "9001:9001"
    networks:
      - messenger_net

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - messenger_net

  app:
    build: ./server
    environment:
      DATABASE_URL: postgresql://messenger:${DB_PASSWORD}@postgres/messenger
      MINIO_ENDPOINT: minio:9000
      MINIO_ACCESS_KEY: ${MINIO_USER}
      MINIO_SECRET_KEY: ${MINIO_PASSWORD}
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379
      JWT_SECRET: ${JWT_SECRET}
      TOTP_ISSUER: LocalMessenger
    depends_on:
      - postgres
      - minio
      - redis
    ports:
      - "8080:8080"
    networks:
      - messenger_net

  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    ports:
      - "443:443"
    depends_on:
      - app
    networks:
      - messenger_net

volumes:
  postgres_data:
  minio_data:
  redis_data:

networks:
  messenger_net:
    driver: bridge
```

---

## 10. Рекомендации по разработке MVP

### Этап 1 (2-3 недели)
- [ ] Настройка инфраструктуры (PostgreSQL, MinIO, Redis)
- [ ] Базовая аутентификация (регистрация, вход, JWT)
- [ ] CRUD пользователей
- [ ] Создание личных чатов

### Этап 2 (3-4 недели)
- [ ] Отправка/получение текстовых сообщений
- [ ] WebSocket для real-time обновлений
- [ ] Статусы онлайн/офлайн
- [ ] Индикатор набора текста

### Этап 3 (3-4 недели)
- [ ] Загрузка медиафайлов в MinIO
- [ ] Отправка изображений, документов
- [ ] Генерация превью
- [ ] Поиск по сообщениям

### Этап 4 (3-4 недели)
- [ ] Группы и каналы
- [ ] Реакции на сообщения
- [ ] Ответы и пересылка
- [ ] Закреплённые сообщения

### Этап 5 (4-5 недель)
- [ ] Голосовые/видеозвонки (WebRTC)
- [ ] Секретные чаты с E2EE
- [ ] Таймер самоуничтожения
- [ ] Боты API

### Этап 6 (2-3 недели)
- [ ] Админ-панель
- [ ] Логирование и аудит
- [ ] Резервное копирование
- [ ] Тестирование и оптимизация

**Общее время разработки MVP: 17-23 недели**

---

## 11. Дополнительные материалы

### 11.1 Рекомендуемые библиотеки

**Go:**
- `github.com/gorilla/websocket` - WebSocket
- `github.com/gin-gonic/gin` - REST API
- `github.com/golang-jwt/jwt` - JWT
- `github.com/pquerna/otp` - TOTP
- `github.com/minio/minio-go` - MinIO клиент

**Python:**
- `aiohttp` - async HTTP/WebSocket
- `pyjwt` - JWT
- `pyotp` - TOTP
- `minio` - MinIO клиент
- `argon2-cffi` - хеширование паролей

**Flutter:**
- `flutter_bloc` - управление состоянием
- `dio` - HTTP клиент
- `web_socket_channel` - WebSocket
- `localstorage` - локальное кэширование
- `flutter_webrtc` - звонки

### 11.2 Производительность

- Использовать пагинацию для сообщений (50-100 на страницу)
- Кэшировать часто запрашиваемые данные в Redis
- Индексы в PostgreSQL для поиска
- CDN для раздачи статики (внутри сети)
- Горизонтальное масштабирование серверов приложений

### 11.3 Мониторинг

- Prometheus + Grafana для метрик
- ELK Stack для логов
- Health check эндпоинты
- Alerting при критических ошибках
