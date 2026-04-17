package service

import (
	"crypto/rand"
	"database/sql"
	"encoding/base64"
	"errors"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"github.com/pquerna/otp/totp"
)

type AuthService struct {
	jwtSecret []byte
}

func NewAuthService(jwtSecret string) *AuthService {
	return &AuthService{
		jwtSecret: []byte(jwtSecret),
	}
}

type Claims struct {
	UserID   int64  `json:"user_id"`
	Username string `json:"username"`
	jwt.RegisteredClaims
}

func (s *AuthService) GenerateTokens(userID int64, username string) (string, string, error) {
	// Access token (15 минут)
	accessToken := jwt.NewWithClaims(jwt.SigningMethodHS256, Claims{
		UserID:   userID,
		Username: username,
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(15 * time.Minute)),
			IssuedAt:  jwt.NewNumericDate(time.Now()),
		},
	})

	accessString, err := accessToken.SignedString(s.jwtSecret)
	if err != nil {
		return "", "", err
	}

	// Refresh token (30 дней)
	refreshToken := jwt.NewWithClaims(jwt.SigningMethodHS256, Claims{
		UserID:   userID,
		Username: username,
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(30 * 24 * time.Hour)),
			IssuedAt:  jwt.NewNumericDate(time.Now()),
		},
	})

	refreshString, err := refreshToken.SignedString(s.jwtSecret)
	if err != nil {
		return "", "", err
	}

	return accessString, refreshString, nil
}

func (s *AuthService) ValidateToken(tokenString string) (*Claims, error) {
	token, err := jwt.ParseWithClaims(tokenString, &Claims{}, func(token *jwt.Token) (interface{}, error) {
		return s.jwtSecret, nil
	})

	if err != nil {
		return nil, err
	}

	if claims, ok := token.Claims.(*Claims); ok && token.Valid {
		return claims, nil
	}

	return nil, errors.New("неверный токен")
}

func (s *AuthService) RefreshToken(refreshToken string) (string, string, error) {
	claims, err := s.ValidateToken(refreshToken)
	if err != nil {
		return "", "", err
	}

	return s.GenerateTokens(claims.UserID, claims.Username)
}

// Генерация секрета для TOTP
func (s *AuthService) GenerateTOTPSecret() (string, error) {
	bytes := make([]byte, 20)
	if _, err := rand.Read(bytes); err != nil {
		return "", err
	}
	return base64.StdEncoding.EncodeToString(bytes), nil
}

// Проверка TOTP кода
func (s *AuthService) VerifyTOTP(secret, code string) bool {
	return totp.Validate(code, secret)
}

// Генерация URI для QR-кода
func (s *AuthService) GetTOTPURI(secret, username, issuer string) string {
	return totp.GenerateURL(totp.GenerateOpts{
		Issuer:      issuer,
		AccountName: username,
		Secret:      secret,
	})
}
