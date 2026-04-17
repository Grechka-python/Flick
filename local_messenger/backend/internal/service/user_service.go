package service

import (
	"database/sql"
	"errors"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"golang.org/x/crypto/bcrypt"
)

type UserService struct {
	db *sql.DB
}

func NewUserService(databaseURL string) *UserService {
	db, err := sql.Open("postgres", databaseURL)
	if err != nil {
		panic(err)
	}
	return &UserService{db: db}
}

func (s *UserService) Create(username, email, password, firstName, lastName string) (int64, error) {
	hash, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	if err != nil {
		return 0, err
	}

	var id int64
	err = s.db.QueryRow(
		`INSERT INTO users (username, email, password_hash, first_name, last_name, created_at, last_seen)
		 VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING id`,
		username, email, string(hash), firstName, lastName, time.Now(), time.Now(),
	).Scan(&id)

	return id, err
}

func (s *UserService) GetByUsername(username string) (*User, error) {
	user := &User{}
	err := s.db.QueryRow(
		`SELECT id, username, email, password_hash, first_name, last_name, avatar_url, phone, 
		        is_admin, two_factor_secret, two_factor_enabled, created_at, last_seen, is_online
		 FROM users WHERE username = $1`,
		username,
	).Scan(
		&user.ID, &user.Username, &user.Email, &user.PasswordHash, &user.FirstName, &user.LastName,
		&user.AvatarURL, &user.Phone, &user.IsAdmin, &user.TwoFactorSecret, &user.TwoFactorEnabled,
		&user.CreatedAt, &user.LastSeen, &user.IsOnline,
	)

	if err == sql.ErrNoRows {
		return nil, errors.New("пользователь не найден")
	}

	return user, err
}

func (s *UserService) GetByID(id int64) (*User, error) {
	user := &User{}
	err := s.db.QueryRow(
		`SELECT id, username, email, password_hash, first_name, last_name, avatar_url, phone, 
		        is_admin, two_factor_secret, two_factor_enabled, created_at, last_seen, is_online
		 FROM users WHERE id = $1`,
		id,
	).Scan(
		&user.ID, &user.Username, &user.Email, &user.PasswordHash, &user.FirstName, &user.LastName,
		&user.AvatarURL, &user.Phone, &user.IsAdmin, &user.TwoFactorSecret, &user.TwoFactorEnabled,
		&user.CreatedAt, &user.LastSeen, &user.IsOnline,
	)

	if err == sql.ErrNoRows {
		return nil, errors.New("пользователь не найден")
	}

	return user, err
}

func (s *UserService) UpdateLastSeen(id int64) error {
	_, err := s.db.Exec("UPDATE users SET last_seen = $1 WHERE id = $2", time.Now(), id)
	return err
}

func (s *UserService) SetOnlineStatus(id int64, online bool) error {
	_, err := s.db.Exec("UPDATE users SET is_online = $1, last_seen = $2 WHERE id = $3", online, time.Now(), id)
	return err
}

func (s *UserService) Enable2FA(id int64, secret string) error {
	_, err := s.db.Exec("UPDATE users SET two_factor_secret = $1, two_factor_enabled = true WHERE id = $2", secret, id)
	return err
}

func (s *UserService) VerifyPassword(hash, password string) bool {
	err := bcrypt.CompareHashAndPassword([]byte(hash), []byte(password))
	return err == nil
}

func (s *UserService) Search(query string, limit int) ([]*User, error) {
	rows, err := s.db.Query(
		`SELECT id, username, email, first_name, last_name, avatar_url, is_online, last_seen
		 FROM users 
		 WHERE username ILIKE $1 OR first_name ILIKE $1 OR last_name ILIKE $1
		 LIMIT $2`,
		"%"+query+"%", limit,
	)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var users []*User
	for rows.Next() {
		user := &User{}
		err := rows.Scan(&user.ID, &user.Username, &user.Email, &user.FirstName, &user.LastName, &user.AvatarURL, &user.IsOnline, &user.LastSeen)
		if err != nil {
			return nil, err
		}
		users = append(users, user)
	}

	return users, rows.Err()
}

// User структура для сервиса (упрощённая версия модели)
type User struct {
	ID               int64     `json:"id"`
	Username         string    `json:"username"`
	Email            string    `json:"email"`
	PasswordHash     string    `json:"-"`
	FirstName        string    `json:"first_name"`
	LastName         string    `json:"last_name"`
	AvatarURL        string    `json:"avatar_url,omitempty"`
	Phone            string    `json:"phone,omitempty"`
	IsAdmin          bool      `json:"is_admin"`
	TwoFactorSecret  string    `json:"-"`
	TwoFactorEnabled bool      `json:"two_factor_enabled"`
	CreatedAt        time.Time `json:"created_at"`
	LastSeen         time.Time `json:"last_seen"`
	IsOnline         bool      `json:"is_online"`
}
