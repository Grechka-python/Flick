package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"local_messenger/internal/config"
	"local_messenger/internal/handler"
	"local_messenger/internal/service"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/gorilla/websocket"
)

var upgrader = websocket.Upgrader{
	ReadBufferSize:  1024,
	WriteBufferSize: 1024,
	CheckOrigin: func(r *http.Request) bool {
		return true // Для локальной сети
	},
}

func main() {
	cfg := config.LoadConfig()

	// Инициализация сервисов
	userService := service.NewUserService(cfg.DatabaseURL)
	messageService := service.NewMessageService(cfg.DatabaseURL)
	fileService := service.NewFileService(cfg.MinIOEndpoint, cfg.MinIOAccessKey, cfg.MinIOSecretKey)
	authService := service.NewAuthService(cfg.JWTSecret)

	// Создание роутера
	r := chi.NewRouter()
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)
	r.Use(middleware.CORS)

	// HTTP обработчики
	h := handler.NewHandler(userService, messageService, fileService, authService)

	r.Route("/api/v1", func(r chi.Router) {
		// Аутентификация
		r.Post("/auth/register", h.Register)
		r.Post("/auth/login", h.Login)
		r.Post("/auth/logout", h.Logout)
		r.Post("/auth/refresh", h.RefreshToken)
		r.Post("/auth/2fa/enable", h.Enable2FA)
		r.Post("/auth/2fa/verify", h.Verify2FA)

		// Пользователи
		r.Get("/users/me", h.GetMe)
		r.Put("/users/me", h.UpdateUser)
		r.Get("/users/{id}", h.GetUser)
		r.Get("/users/search", h.SearchUsers)
		r.Get("/users/sessions", h.GetSessions)
		r.Delete("/users/sessions/{session_id}", h.DeleteSession)

		// Чаты
		r.Post("/chats", h.CreateChat)
		r.Get("/chats", h.GetChats)
		r.Get("/chats/{id}", h.GetChat)
		r.Put("/chats/{id}", h.UpdateChat)
		r.Delete("/chats/{id}", h.DeleteChat)
		r.Post("/chats/{id}/members", h.AddMember)
		r.Delete("/chats/{id}/members/{user_id}", h.RemoveMember)

		// Сообщения
		r.Get("/chats/{id}/messages", h.GetMessages)
		r.Post("/chats/{id}/messages", h.SendMessage)
		r.Put("/chats/{id}/messages/{msg_id}", h.EditMessage)
		r.Delete("/chats/{id}/messages/{msg_id}", h.DeleteMessage)
		r.Post("/chats/{id}/messages/{msg_id}/read", h.MarkAsRead)
		r.Post("/chats/{id}/messages/{msg_id}/reaction", h.AddReaction)
		r.Post("/chats/{id}/messages/{msg_id}/forward", h.ForwardMessage)
		r.Post("/chats/{id}/messages/{msg_id}/reply", h.ReplyToMessage)

		// Медиа и файлы
		r.Post("/upload", h.UploadFile)
		r.Get("/files/{file_id}", h.GetFile)

		// Поиск
		r.Get("/search", h.Search)

		// Администрирование
		r.Post("/admin/users", h.AdminCreateUser)
		r.Delete("/admin/users/{id}", h.AdminDeleteUser)
		r.Get("/admin/logs", h.AdminGetLogs)
		r.Post("/admin/backup", h.AdminBackup)
	})

	// WebSocket для real-time сообщений
	r.HandleFunc("/ws", h.WebSocketHandler)

	// Запуск сервера
	srv := &http.Server{
		Addr:         fmt.Sprintf(":%s", cfg.ServerPort),
		Handler:      r,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	go func() {
		log.Printf("Сервер запущен на порту %s", cfg.ServerPort)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Ошибка запуска сервера: %v", err)
		}
	}()

	// Graceful shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Println("Остановка сервера...")
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		log.Fatalf("Ошибка остановки сервера: %v", err)
	}

	log.Println("Сервер остановлен")
}
