# Local Messenger - Локальный мессенджер с функционалом Telegram

Полнофункциональный локальный мессенджер для работы внутри закрытой сети.

## 📋 Возможности

### Функциональные требования (как в Telegram)
- ✅ Личные сообщения (текст, эмодзи, реакции)
- ✅ Редактирование/удаление сообщений (48 часов)
- ✅ Ответы, пересылка, цитирование
- ✅ Медиафайлы до 2 ГБ (изображения, видео, аудио, документы)
- ✅ Группы (до 200 участников)
- ✅ Каналы (неограниченная аудитория)
- ✅ Голосовые и видеозвонки (WebRTC)
- ✅ Секретные чаты с таймером самоуничтожения
- ✅ Поиск по сообщениям (русский/английский)
- ✅ Управление сессиями
- ✅ Боты (API для создания)
- ✅ Административные функции

### Технические характеристики
- **Сервер**: FastAPI (Python asyncio)
- **База данных**: PostgreSQL + MinIO (объектное хранилище)
- **Real-time**: WebSocket
- **Аутентификация**: JWT + TOTP (2FA)
- **Шифрование**: TLS 1.3

## 🚀 Быстрый старт

### Предварительные требования
- Python 3.9+
- PostgreSQL 13+
- Redis (опционально, для кэширования)
- MinIO (для хранения файлов)

### Установка

1. **Клонирование репозитория**
```bash
cd /workspace/local_messenger
```

2. **Установка зависимостей**
```bash
pip install -r requirements.txt
```

3. **Настройка переменных окружения**
```bash
cp .env.example .env
# Отредактируйте .env с вашими настройками
```

4. **Запуск базы данных (Docker)**
```bash
docker-compose up -d postgres minio redis
```

5. **Инициализация БД**
```bash
python -m app.db.init_db
```

6. **Запуск сервера**
```bash
# Режим разработки
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Продакшен режим
python -m app.main
```

## 📁 Структура проекта

```
local_messenger/
├── app/
│   ├── api/
│   │   └── routes.py          # REST API endpoints
│   ├── core/
│   │   ├── config.py          # Настройки приложения
│   │   ├── security.py        # Аутентификация, JWT, TOTP
│   │   └── websocket_manager.py  # WebSocket менеджер
│   ├── db/
│   │   └── session.py         # Подключение к БД
│   ├── models/
│   │   └── __init__.py        # SQLAlchemy модели
│   ├── schemas/
│   │   └── __init__.py        # Pydantic схемы
│   ├── services/
│   │   ├── user_service.py    # Сервис пользователей
│   │   └── chat_service.py    # Сервис чатов и сообщений
│   ├── static/
│   │   └── styles.css         # CSS стили GUI
│   └── main.py                # Точка входа
├── docs/
│   └── TECHNICAL_SPECIFICATION.md  # Полная спецификация
├── requirements.txt
├── docker-compose.yml
└── README.md
```

## 🔌 API Endpoints

### Аутентификация
- `POST /api/v1/auth/register` - Регистрация
- `POST /api/v1/auth/login` - Вход
- `GET /api/v1/auth/sessions` - Список сессий
- `DELETE /api/v1/auth/sessions/{id}` - Удаление сессии

### Пользователи
- `GET /api/v1/users/me` - Текущий пользователь
- `PUT /api/v1/users/me` - Обновление профиля
- `POST /api/v1/users/search` - Поиск пользователей

### Чаты
- `GET /api/v1/chats` - Список чатов
- `POST /api/v1/chats` - Создание чата
- `GET /api/v1/chats/{id}` - Информация о чате
- `POST /api/v1/chats/{id}/members` - Добавить участника

### Сообщения
- `GET /api/v1/chats/{id}/messages` - История сообщений
- `POST /api/v1/chats/{id}/messages` - Отправить сообщение
- `PUT /api/v1/messages/{id}` - Редактировать
- `DELETE /api/v1/messages/{id}` - Удалить
- `POST /api/v1/messages/{id}/reactions` - Реакция

### WebSocket
- `ws://localhost:8000/ws?token={jwt_token}` - Real-time подключения

## 🎨 GUI Стиль

Цветовая схема соответствует требованиям:
- **Основной цвет**: Глубокий синий (#0A2F6C)
- **Акцентный цвет**: Яркий оранжевый (#FF8C42)
- **Фон**: Градиент от тёмно-синего до угольно-чёрного
- **Текст**: Белый и светло-серый
- **Иконки**: Белые, оранжевые при наведении

## 🔒 Безопасность

- Пароли хешируются bcrypt
- JWT токены с ограниченным временем жизни
- TOTP для двухфакторной аутентификации
- TLS 1.3 для шифрования соединения
- Валидация всех входных данных

## 📊 База данных

Основные таблицы:
- `users` - пользователи
- `sessions` - активные сессии
- `chats` - чаты, группы, каналы
- `chat_members` - участники чатов
- `messages` - сообщения
- `media` - медиафайлы
- `reactions` - реакции
- `read_receipts` - статусы прочтения
- `secret_chats` - секретные чаты

## 🧪 Тестирование

```bash
# Запуск тестов
pytest

# Проверка типов
mypy app/

# Линтинг
flake8 app/
```

## 📝 Лицензия

Проект создан для образовательных целей.

## 🤝 Вклад

1. Fork репозиторий
2. Создайте feature branch
3. Commit изменения
4. Push в branch
5. Создайте Pull Request

---

**Версия**: 1.0.0 (MVP)  
**Статус**: Разработка
