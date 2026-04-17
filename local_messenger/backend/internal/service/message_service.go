package service

import (
	"database/sql"
	"time"
)

type MessageService struct {
	db *sql.DB
}

func NewMessageService(databaseURL string) *MessageService {
	db, err := sql.Open("postgres", databaseURL)
	if err != nil {
		panic(err)
	}
	return &MessageService{db: db}
}

func (s *MessageService) Create(chatID, senderID int64, content string, messageType string, mediaID, replyToID *int64) (*Message, error) {
	msg := &Message{}
	now := time.Now()

	err := s.db.QueryRow(
		`INSERT INTO messages (chat_id, sender_id, content, type, media_id, reply_to_id, created_at)
		 VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING id, chat_id, sender_id, content, type, media_id, reply_to_id, created_at`,
		chatID, senderID, content, messageType, mediaID, replyToID, now,
	).Scan(&msg.ID, &msg.ChatID, &msg.SenderID, &msg.Content, &msg.Type, &msg.MediaID, &msg.ReplyToID, &msg.CreatedAt)

	if err != nil {
		return nil, err
	}

	msg.CreatedAt = now
	return msg, nil
}

func (s *MessageService) GetByChatID(chatID int64, limit, offset int) ([]*Message, error) {
	rows, err := s.db.Query(
		`SELECT id, chat_id, sender_id, content, type, media_id, reply_to_id, edited_at, is_pinned, created_at
		 FROM messages
		 WHERE chat_id = $1 AND deleted_at IS NULL
		 ORDER BY created_at DESC
		 LIMIT $2 OFFSET $3`,
		chatID, limit, offset,
	)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var messages []*Message
	for rows.Next() {
		msg := &Message{}
		err := rows.Scan(&msg.ID, &msg.ChatID, &msg.SenderID, &msg.Content, &msg.Type, &msg.MediaID, &msg.ReplyToID, &msg.EditedAt, &msg.IsPinned, &msg.CreatedAt)
		if err != nil {
			return nil, err
		}
		messages = append(messages, msg)
	}

	return messages, rows.Err()
}

func (s *MessageService) GetByID(id int64) (*Message, error) {
	msg := &Message{}
	err := s.db.QueryRow(
		`SELECT id, chat_id, sender_id, content, type, media_id, reply_to_id, edited_at, is_pinned, created_at
		 FROM messages WHERE id = $1 AND deleted_at IS NULL`,
		id,
	).Scan(&msg.ID, &msg.ChatID, &msg.SenderID, &msg.Content, &msg.Type, &msg.MediaID, &msg.ReplyToID, &msg.EditedAt, &msg.IsPinned, &msg.CreatedAt)

	if err == sql.ErrNoRows {
		return nil, sql.ErrNoRows
	}

	return msg, err
}

func (s *MessageService) Update(id int64, content string) error {
	now := time.Now()
	_, err := s.db.Exec(
		`UPDATE messages SET content = $1, edited_at = $2 WHERE id = $3`,
		content, now, id,
	)
	return err
}

func (s *MessageService) Delete(id int64) error {
	now := time.Now()
	_, err := s.db.Exec(`UPDATE messages SET deleted_at = $1 WHERE id = $2`, now, id)
	return err
}

func (s *MessageService) MarkAsRead(messageID, userID int64) error {
	_, err := s.db.Exec(
		`INSERT INTO message_reads (message_id, user_id, read_at) VALUES ($1, $2, $3)
		 ON CONFLICT (message_id, user_id) DO NOTHING`,
		messageID, userID, time.Now(),
	)
	return err
}

func (s *MessageService) AddReaction(messageID, userID int64, emoji string) error {
	_, err := s.db.Exec(
		`INSERT INTO reactions (message_id, user_id, emoji, created_at) VALUES ($1, $2, $3, $4)
		 ON CONFLICT (message_id, user_id, emoji) DO UPDATE SET created_at = $4`,
		messageID, userID, emoji, time.Now(),
	)
	return err
}

func (s *MessageService) RemoveReaction(messageID, userID int64, emoji string) error {
	_, err := s.db.Exec(
		`DELETE FROM reactions WHERE message_id = $1 AND user_id = $2 AND emoji = $3`,
		messageID, userID, emoji,
	)
	return err
}

func (s *MessageService) Forward(messageID, newChatID, senderID int64) (*Message, error) {
	originalMsg, err := s.GetByID(messageID)
	if err != nil {
		return nil, err
	}

	return s.Create(newChatID, senderID, originalMsg.Content, string(originalMsg.Type), originalMsg.MediaID, nil)
}

func (s *MessageService) Search(query string, chatID, senderID *int64, messageType *string, fromDate, toDate *time.Time, limit, offset int) ([]*Message, error) {
	whereClause := "WHERE deleted_at IS NULL"
	args := []interface{}{}
	argIndex := 1

	if query != "" {
		args = append(args, "%"+query+"%")
		whereClause += " AND content ILIKE $" + string(rune(argIndex))
		argIndex++
	}

	if chatID != nil {
		args = append(args, *chatID)
		whereClause += " AND chat_id = $" + string(rune(argIndex))
		argIndex++
	}

	if senderID != nil {
		args = append(args, *senderID)
		whereClause += " AND sender_id = $" + string(rune(argIndex))
		argIndex++
	}

	if messageType != nil {
		args = append(args, *messageType)
		whereClause += " AND type = $" + string(rune(argIndex))
		argIndex++
	}

	if fromDate != nil {
		args = append(args, *fromDate)
		whereClause += " AND created_at >= $" + string(rune(argIndex))
		argIndex++
	}

	if toDate != nil {
		args = append(args, *toDate)
		whereClause += " AND created_at <= $" + string(rune(argIndex))
		argIndex++
	}

	args = append(args, limit, offset)

	rows, err := s.db.Query(
		`SELECT id, chat_id, sender_id, content, type, media_id, reply_to_id, edited_at, is_pinned, created_at
		 FROM messages `+whereClause+`
		 ORDER BY created_at DESC
		 LIMIT $`+string(rune(argIndex-1))+` OFFSET $`+string(rune(argIndex)),
		args...,
	)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var messages []*Message
	for rows.Next() {
		msg := &Message{}
		err := rows.Scan(&msg.ID, &msg.ChatID, &msg.SenderID, &msg.Content, &msg.Type, &msg.MediaID, &msg.ReplyToID, &msg.EditedAt, &msg.IsPinned, &msg.CreatedAt)
		if err != nil {
			return nil, err
		}
		messages = append(messages, msg)
	}

	return messages, rows.Err()
}

// Message структура для сервиса
type Message struct {
	ID          int64      `json:"id"`
	ChatID      int64      `json:"chat_id"`
	SenderID    int64      `json:"sender_id"`
	Content     string     `json:"content"`
	Type        string     `json:"type"`
	MediaID     *int64     `json:"media_id,omitempty"`
	ReplyToID   *int64     `json:"reply_to_id,omitempty"`
	EditedAt    *time.Time `json:"edited_at,omitempty"`
	IsPinned    bool       `json:"is_pinned"`
	CreatedAt   time.Time  `json:"created_at"`
}
