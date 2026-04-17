package model

import (
	"time"
)

// Пользователь
type User struct {
	ID            int64     `json:"id"`
	Username      string    `json:"username"`
	Email         string    `json:"email"`
	PasswordHash  string    `json:"-"`
	FirstName     string    `json:"first_name"`
	LastName      string    `json:"last_name"`
	AvatarURL     string    `json:"avatar_url,omitempty"`
	Phone         string    `json:"phone,omitempty"`
	IsAdmin       bool      `json:"is_admin"`
	TwoFactorSecret string  `json:"-"`
	TwoFactorEnabled bool   `json:"two_factor_enabled"`
	CreatedAt     time.Time `json:"created_at"`
	LastSeen      time.Time `json:"last_seen"`
	IsOnline      bool      `json:"is_online"`
}

// Сессия пользователя
type Session struct {
	ID           string    `json:"id"`
	UserID       int64     `json:"user_id"`
	DeviceName   string    `json:"device_name"`
	DeviceType   string    `json:"device_type"` // web, android, ios, desktop
	IPAddress    string    `json:"ip_address"`
	UserAgent    string    `json:"user_agent"`
	RefreshToken string    `json:"-"`
	ExpiresAt    time.Time `json:"expires_at"`
	CreatedAt    time.Time `json:"created_at"`
	LastActive   time.Time `json:"last_active"`
}

// Тип чата
type ChatType string

const (
	ChatTypePrivate   ChatType = "private"
	ChatTypeGroup     ChatType = "group"
	ChatTypeChannel   ChatType = "channel"
	ChatTypeSecret    ChatType = "secret"
)

// Чат
type Chat struct {
	ID              int64     `json:"id"`
	Type            ChatType  `json:"type"`
	Name            string    `json:"name,omitempty"`
	Description     string    `json:"description,omitempty"`
	AvatarURL       string    `json:"avatar_url,omitempty"`
	OwnerID         int64     `json:"owner_id"`
	IsReadOnly      bool      `json:"is_read_only"`
	MaxMembers      int       `json:"max_members"` // 200 для групп, 0 для каналов (неограниченно)
	LocalInviteCode string    `json:"local_invite_code"`
	QRCodeData      string    `json:"qr_code_data"`
	CreatedAt       time.Time `json:"created_at"`
	UpdatedAt       time.Time `json:"updated_at"`
	LastMessageID   *int64    `json:"last_message_id,omitempty"`
	UnreadCount     int       `json:"unread_count"`
}

// Участник чата
type ChatMember struct {
	ChatID     int64     `json:"chat_id"`
	UserID     int64     `json:"user_id"`
	Role       string    `json:"role"` // owner, admin, member
	JoinedAt   time.Time `json:"joined_at"`
	CanSend    bool      `json:"can_send"`
	CanEdit    bool      `json:"can_edit"`
	CanDelete  bool      `json:"can_delete"`
	CanInvite  bool      `json:"can_invite"`
}

// Тип сообщения
type MessageType string

const (
	MessageTypeText     MessageType = "text"
	MessageTypeImage    MessageType = "image"
	MessageTypeVideo    MessageType = "video"
	MessageTypeAudio    MessageType = "audio"
	MessageTypeFile     MessageType = "file"
	MessageTypeVoice    MessageType = "voice"
	MessageTypeSystem   MessageType = "system"
)

// Сообщение
type Message struct {
	ID            int64            `json:"id"`
	ChatID        int64            `json:"chat_id"`
	SenderID      int64            `json:"sender_id"`
	Content       string           `json:"content"`
	Type          MessageType      `json:"type"`
	MediaID       *int64           `json:"media_id,omitempty"`
	ReplyToID     *int64           `json:"reply_to_id,omitempty"`
	EditedAt      *time.Time       `json:"edited_at,omitempty"`
	DeletedAt     *time.Time       `json:"deleted_at,omitempty"`
	IsPinned      bool             `json:"is_pinned"`
	Reactions     []Reaction       `json:"reactions,omitempty"`
	ReadBy        []int64          `json:"read_by,omitempty"`
	DeliveredAt   *time.Time       `json:"delivered_at,omitempty"`
	ReadAt        *time.Time       `json:"read_at,omitempty"`
	CreatedAt     time.Time        `json:"created_at"`
	ExpiresAt     *time.Time       `json:"expires_at,omitempty"` // Для секретных чатов
	ForwardedFrom *int64           `json:"forwarded_from,omitempty"`
}

// Реакция на сообщение
type Reaction struct {
	UserID    int64     `json:"user_id"`
	Emoji     string    `json:"emoji"` // 👍, ❤️, 🔥, etc.
	CreatedAt time.Time `json:"created_at"`
}

// Медиафайл
type Media struct {
	ID          int64     `json:"id"`
	UserID      int64     `json:"user_id"`
	FileType    string    `json:"file_type"` // image, video, audio, document
	MimeType    string    `json:"mime_type"`
	FileName    string    `json:"file_name"`
	FileSize    int64     `json:"file_size"` // до 2GB
	FilePath    string    `json:"file_path"` // путь в MinIO
	ThumbnailPath string  `json:"thumbnail_path,omitempty"`
	Width       int       `json:"width,omitempty"`
	Height      int       `json:"height,omitempty"`
	Duration    int       `json:"duration,omitempty"` // для аудио/видео в секундах
	IsCompressed bool     `json:"is_compressed"`
	CreatedAt   time.Time `json:"created_at"`
}

// Лог аудита (метаданные)
type AuditLog struct {
	ID          int64     `json:"id"`
	UserID      int64     `json:"user_id"`
	Action      string    `json:"action"` // login, logout, message_sent, file_uploaded, etc.
	TargetType  string    `json:"target_type"` // user, chat, message, file
	TargetID    *int64    `json:"target_id"`
	IPAddress   string    `json:"ip_address"`
	UserAgent   string    `json:"user_agent"`
	CreatedAt   time.Time `json:"created_at"`
}

// Запрос на регистрацию
type RegisterRequest struct {
	Username  string `json:"username"`
	Email     string `json:"email"`
	Password  string `json:"password"`
	FirstName string `json:"first_name"`
	LastName  string `json:"last_name"`
}

// Запрос на вход
type LoginRequest struct {
	Username string `json:"username"`
	Password string `json:"password"`
	TOTPCode string `json:"totp_code,omitempty"`
}

// Токены аутентификации
type AuthTokens struct {
	AccessToken  string `json:"access_token"`
	RefreshToken string `json:"refresh_token"`
	ExpiresIn    int    `json:"expires_in"`
}

// Запрос на создание чата
type CreateChatRequest struct {
	Type       ChatType `json:"type"`
	Name       string   `json:"name,omitempty"`
	MemberIDs  []int64  `json:"member_ids,omitempty"`
	IsReadOnly bool     `json:"is_read_only"`
}

// Запрос на отправку сообщения
type SendMessageRequest struct {
	Content   string  `json:"content"`
	Type      MessageType `json:"type"`
	MediaID   *int64  `json:"media_id,omitempty"`
	ReplyToID *int64  `json:"reply_to_id,omitempty"`
}

// Запрос на реакцию
type ReactionRequest struct {
	Emoji string `json:"emoji"`
}

// Поиск сообщений
type SearchRequest struct {
	Query      string    `json:"query"`
	ChatID     *int64    `json:"chat_id,omitempty"`
	SenderID   *int64    `json:"sender_id,omitempty"`
	MessageType *MessageType `json:"message_type,omitempty"`
	FromDate   *time.Time `json:"from_date,omitempty"`
	ToDate     *time.Time `json:"to_date,omitempty"`
	Limit      int       `json:"limit"`
	Offset     int       `json:"offset"`
}

// WebSocket сообщение
type WSMessage struct {
	Type      string      `json:"type"` // new_message, message_read, user_online, etc.
	Payload   interface{} `json:"payload"`
	Timestamp time.Time   `json:"timestamp"`
}
