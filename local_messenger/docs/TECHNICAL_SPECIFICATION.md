# Техническая спецификация локального мессенджера (MVP)

## 1. Функциональные требования

### 1.1 Личные сообщения
- Отправка текста, эмодзи, реакций (лайк, сердечко и т.д.)
- Редактирование/удаление сообщений за последние 48 часов
- Ответы на конкретные сообщения
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
- Синхронизация истории между устройствами
- Лимит: 10 ГБ на пользователя (расширяется)

### 1.7 Поиск
- По тексту (русский/английский)
- По датам, типу медиа, отправителю

### 1.8 Управление сессиями
- Список активных устройств
- Удаление сессий

### 1.9 Секретные чаты
- Device-to-device шифрование
- Без облачного бэкапа
- Таймер самоуничтожения (5 сек - 1 неделя)

### 1.10 Боты
- API для создания локальных ботов
- Работа как отдельные аккаунты

### 1.11 Административные функции
- Создание/удаление пользователей
- Резервное копирование
- Логирование метаданных

## 2. Технические ограничения

- Хранение данных: только локальный сервер
- Аутентификация: логин/пароль + TOTP (2FA)
- Протокол: TCP/WebSocket с TLS 1.3
- Секретные чаты: Double Ratchet алгоритм
- БД: PostgreSQL (метаданные) + MinIO (файлы)
- Клиенты: кроссплатформенные (описание архитектуры)

## 3. Схема базы данных

```sql
-- Таблица пользователей
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20),
    avatar_url TEXT,
    totp_secret VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    storage_quota BIGINT DEFAULT 10737418240, -- 10 GB
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen TIMESTAMP WITH TIME ZONE
);

-- Таблица сессий
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    device_name VARCHAR(100),
    device_type VARCHAR(20), -- 'desktop', 'mobile', 'web'
    ip_address INET,
    access_token_hash VARCHAR(255) NOT NULL,
    refresh_token_hash VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Таблица чатов (личные, группы, каналы)
CREATE TABLE chats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_type VARCHAR(20) NOT NULL, -- 'private', 'group', 'channel'
    name VARCHAR(255),
    description TEXT,
    avatar_url TEXT,
    owner_id UUID REFERENCES users(id),
    max_participants INTEGER DEFAULT 200,
    is_read_only BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Участники чатов
CREATE TABLE chat_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id UUID REFERENCES chats(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) DEFAULT 'member', -- 'owner', 'admin', 'member'
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(chat_id, user_id)
);

-- Сообщения
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id UUID REFERENCES chats(id) ON DELETE CASCADE,
    sender_id UUID REFERENCES users(id),
    content TEXT,
    message_type VARCHAR(20) DEFAULT 'text', -- 'text', 'image', 'video', 'audio', 'document'
    reply_to_id UUID REFERENCES messages(id),
    forwarded_from_id UUID REFERENCES messages(id),
    edited_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    is_pinned BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Реакции на сообщения
CREATE TABLE reactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    emoji VARCHAR(10) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(message_id, user_id)
);

-- Медиафайлы
CREATE TABLE media (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100),
    thumbnail_path TEXT,
    width INTEGER,
    height INTEGER,
    duration INTEGER, -- для аудио/видео в секундах
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Секретные чаты
CREATE TABLE secret_chats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user1_id UUID REFERENCES users(id),
    user2_id UUID REFERENCES users(id),
    encryption_key_hash VARCHAR(255),
    self_destruct_timer INTEGER, -- в секундах
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Статусы прочтения
CREATE TABLE read_receipts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    read_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(message_id, user_id)
);

-- Индексы для поиска
CREATE INDEX idx_messages_content ON messages USING gin(to_tsvector('russian', content));
CREATE INDEX idx_messages_created_at ON messages(created_at);
CREATE INDEX idx_messages_sender_id ON messages(sender_id);
CREATE INDEX idx_chat_members_user_id ON chat_members(user_id);
```

## 4. API Endpoints

### REST API

#### Аутентификация
- `POST /api/v1/auth/register` - Регистрация пользователя
- `POST /api/v1/auth/login` - Вход (возвращает токены)
- `POST /api/v1/auth/logout` - Выход
- `POST /api/v1/auth/refresh` - Обновление токена
- `POST /api/v1/auth/2fa/verify` - Проверка TOTP кода
- `GET /api/v1/auth/sessions` - Список активных сессий
- `DELETE /api/v1/auth/sessions/{session_id}` - Удаление сессии

#### Пользователи
- `GET /api/v1/users/me` - Текущий пользователь
- `PUT /api/v1/users/me` - Обновление профиля
- `GET /api/v1/users/{user_id}` - Информация о пользователе
- `POST /api/v1/users/search` - Поиск пользователей

#### Чаты
- `GET /api/v1/chats` - Список чатов пользователя
- `POST /api/v1/chats` - Создание чата/группы/канала
- `GET /api/v1/chats/{chat_id}` - Информация о чате
- `PUT /api/v1/chats/{chat_id}` - Обновление чата
- `DELETE /api/v1/chats/{chat_id}` - Удаление чата
- `POST /api/v1/chats/{chat_id}/members` - Добавить участника
- `DELETE /api/v1/chats/{chat_id}/members/{user_id}` - Удалить участника
- `PUT /api/v1/chats/{chat_id}/members/{user_id}/role` - Изменить роль

#### Сообщения
- `GET /api/v1/chats/{chat_id}/messages` - История сообщений (с пагинацией)
- `POST /api/v1/chats/{chat_id}/messages` - Отправить сообщение
- `PUT /api/v1/messages/{message_id}` - Редактировать сообщение
- `DELETE /api/v1/messages/{message_id}` - Удалить сообщение
- `POST /api/v1/messages/{message_id}/reactions` - Добавить реакцию
- `DELETE /api/v1/messages/{message_id}/reactions` - Удалить реакцию
- `POST /api/v1/messages/{message_id}/read` - Отметить как прочитанное
- `POST /api/v1/messages/{message_id}/pin` - Закрепить сообщение
- `DELETE /api/v1/messages/{message_id}/pin` - Открепить сообщение

#### Медиа
- `POST /api/v1/media/upload` - Загрузка файла
- `GET /api/v1/media/{media_id}` - Получение файла
- `DELETE /api/v1/media/{media_id}` - Удаление файла

#### Секретные чаты
- `POST /api/v1/secret-chats` - Создать секретный чат
- `GET /api/v1/secret-chats` - Список секретных чатов
- `DELETE /api/v1/secret-chats/{chat_id}` - Завершить секретный чат
- `PUT /api/v1/secret-chats/{chat_id}/timer` - Установить таймер

#### Поиск
- `GET /api/v1/search/messages` - Поиск по сообщениям
- `GET /api/v1/search/chats` - Поиск по чатам
- `GET /api/v1/search/media` - Поиск по медиа

#### Администрирование
- `POST /api/v1/admin/users` - Создать пользователя
- `DELETE /api/v1/admin/users/{user_id}` - Удалить пользователя
- `GET /api/v1/admin/logs` - Логи метаданных
- `POST /api/v1/admin/backup` - Создать резервную копию

### WebSocket Events

#### Подключение
- Клиент подключается к `ws://server/ws` с токеном авторизации

#### События от сервера к клиенту
- `new_message` - Новое сообщение в чате
- `message_updated` - Сообщение обновлено
- `message_deleted` - Сообщение удалено
- `user_online` - Пользователь онлайн
- `user_offline` - Пользователь оффлайн
- `typing_status` - Статус набора текста
- `read_receipt` - Сообщение прочитано
- `reaction_added` - Добавлена реакция
- `reaction_removed` - Удалена реакция
- `chat_updated` - Чат обновлён
- `member_added` - Участник добавлен
- `member_removed` - Участник удалён
- `call_incoming` - Входящий звонок
- `call_ended` - Звонок завершён

#### События от клиента к серверу
- `send_message` - Отправить сообщение
- `edit_message` - Редактировать сообщение
- `delete_message` - Удалить сообщение
- `add_reaction` - Добавить реакцию
- `mark_read` - Отметить прочитанным
- `typing_start` - Начал набор текста
- `typing_stop` - Закончил набор текста
- `call_start` - Начать звонок
- `call_end` - Завершить звонок
- `subscribe_chat` - Подписаться на обновления чата
- `unsubscribe_chat` - Отписаться от чата

## 5. Алгоритм отправки сообщения

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Клиент А  │────▶│ Локальный    │────▶│   Клиент Б  │
│             │     │    Сервер    │     │             │
└─────────────┘     └──────────────┘     └─────────────┘
       │                    │                    │
       │  1. Отправить      │                    │
       │     сообщение      │                    │
       │───────────────────▶│                    │
       │                    │  2. Валидация      │
       │                    │     токена         │
       │                    │  3. Сохранение     │
       │                    │     в БД           │
       │                    │  4. Загрузка       │
       │                    │     медиа (если    │
       │                    │     есть) в MinIO  │
       │                    │                    │
       │                    │  5. Отправка через │
       │                    │     WebSocket      │
       │                    │───────────────────▶│
       │                    │                    │  6. Отображение
       │                    │                    │
       │  7. Подтверждение  │                    │
       │     доставки       │                    │
       │◀───────────────────│                    │
       │                    │                    │
```

**Детальные шаги:**

1. **Клиент А**:
   - Пользователь вводит текст/выбирает файл
   - Клиент создаёт объект сообщения с временным ID
   - Сообщение шифруется (TLS 1.3)
   - Отправка через POST /api/v1/chats/{id}/messages или WebSocket

2. **Сервер**:
   - Проверка доступа к чату
   - Валидация размера файлов (< 2 ГБ)
   - Сохранение метаданных в PostgreSQL
   - Загрузка файлов в MinIO (если есть медиа)
   - Генерация постоянного ID сообщения
   - Отправка события `new_message` всем участникам чата через WebSocket
   - Отправка подтверждения клиенту А

3. **Клиент Б**:
   - Получение события через WebSocket
   - Дешифровка и отображение сообщения
   - Автоматическая отправка `read_receipt` если чат активен

## 6. Структуры данных (Python)

См. файлы в директории `app/models/` и `app/schemas/`.
