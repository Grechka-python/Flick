# Local Messenger — Локальный мессенджер

Полнофункциональный мессенджер для работы в закрытой локальной сети с дизайном в сине-оранжевых тонах.

## 🎨 Дизайн

- **Основной цвет**: Глубокий синий (#0A2F6C)
- **Акцентный цвет**: Яркий оранжевый (#FF8C42)
- **Фон**: Градиенты от тёмно-синего до угольно-чёрного
- **Текст**: Белый и светло-серый

## 🚀 Функционал

### Личные сообщения
- Отправка текста, эмодзи, реакций
- Редактирование/удаление сообщений (48 часов)
- Ответы на сообщения, пересылка, цитирование

### Медиафайлы
- Изображения, видео, аудио, документы до 2 ГБ
- Сжатие изображений по желанию

### Звонки
- Голосовые и видеозвонки с end-to-end шифрованием
- Адаптивное качество до 4K

### Группы и каналы
- Группы до 200 участников
- Каналы с неограниченной аудиторией
- Приглашения по ID/QR-коду

### Безопасность
- TOTP двухфакторная аутентификация
- Секретные чаты с таймером самоуничтожения
- Шифрование TLS 1.3

## 🏗️ Архитектура

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Flutter   │────▶│   Go Backend │────▶│ PostgreSQL  │
│   Frontend  │◀────│   (REST+WS)  │◀────│   + MinIO   │
└─────────────┘     └──────────────┘     └─────────────┘
```

## 📦 Установка и запуск

### Требования
- Docker и Docker Compose
- Flutter SDK (для фронтенда)
- Go 1.21+ (для бэкенда)

### Запуск через Docker Compose

```bash
cd local_messenger
docker-compose up -d
```

Сервисы будут доступны:
- Backend API: http://localhost:8080
- PostgreSQL: localhost:5432
- MinIO Console: http://localhost:9001

### Сборка фронтенда

```bash
cd frontend
flutter pub get
flutter run
```

## 🔑 API Endpoints

### Аутентификация
- `POST /api/v1/auth/register` — Регистрация
- `POST /api/v1/auth/login` — Вход
- `POST /api/v1/auth/logout` — Выход
- `POST /api/v1/auth/refresh` — Обновление токена
- `POST /api/v1/auth/2fa/enable` — Включение 2FA
- `POST /api/v1/auth/2fa/verify` — Проверка 2FA

### Пользователи
- `GET /api/v1/users/me` — Текущий пользователь
- `PUT /api/v1/users/me` — Обновление профиля
- `GET /api/v1/users/{id}` — Информация о пользователе
- `GET /api/v1/users/search?q=query` — Поиск пользователей

### Чаты
- `POST /api/v1/chats` — Создание чата
- `GET /api/v1/chats` — Список чатов
- `GET /api/v1/chats/{id}` — Информация о чате
- `DELETE /api/v1/chats/{id}` — Удаление чата

### Сообщения
- `GET /api/v1/chats/{id}/messages` — История сообщений
- `POST /api/v1/chats/{id}/messages` — Отправка сообщения
- `PUT /api/v1/chats/{id}/messages/{msg_id}` — Редактирование
- `DELETE /api/v1/chats/{id}/messages/{msg_id}` — Удаление
- `POST /api/v1/chats/{id}/messages/{msg_id}/reaction` — Реакция

### Файлы
- `POST /api/v1/upload` — Загрузка файла
- `GET /api/v1/files/{file_id}` — Получение файла

### WebSocket
- `WS /ws` — Real-time обновления

## 📁 Структура проекта

```
local_messenger/
├── backend/
│   ├── cmd/
│   │   └── server.go          # Точка входа
│   ├── internal/
│   │   ├── config/            # Конфигурация
│   │   ├── handler/           # HTTP обработчики
│   │   ├── model/             # Модели данных
│   │   └── service/           # Бизнес-логика
│   ├── init.sql               # SQL схема БД
│   ├── go.mod                 # Go зависимости
│   └── Dockerfile
├── frontend/
│   ├── lib/
│   │   ├── main.dart          # Точка входа
│   │   ├── theme/             # Темы и цвета
│   │   ├── screens/           # Экраны приложения
│   │   ├── widgets/           # UI компоненты
│   │   └── services/          # API клиенты
│   └── pubspec.yaml
├── docker-compose.yml
└── README.md
```

## 🔐 Администратор по умолчанию

- **Логин**: admin
- **Пароль**: admin123

## 📝 Лицензия

Проект создан для использования в закрытых локальных сетях.
