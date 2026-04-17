package handler

import (
"encoding/json"
"net/http"
"strconv"

"local_messenger/internal/service"

"github.com/go-chi/chi/v5"
"github.com/gorilla/websocket"
)

type Handler struct {
userService    *service.UserService
messageService *service.MessageService
fileService    *service.FileService
authService    *service.AuthService
wsClients      map[int64]*websocket.Conn
}

func NewHandler(userService *service.UserService, messageService *service.MessageService, 
fileService *service.FileService, authService *service.AuthService) *Handler {
return &Handler{
userService:    userService,
messageService: messageService,
fileService:    fileService,
authService:    authService,
wsClients:      make(map[int64]*websocket.Conn),
}
}

func (h *Handler) Register(w http.ResponseWriter, r *http.Request) {
var req service.RegisterRequest
if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
http.Error(w, err.Error(), http.StatusBadRequest)
return
}

id, err := h.userService.Create(req.Username, req.Email, req.Password, req.FirstName, req.LastName)
if err != nil {
http.Error(w, err.Error(), http.StatusInternalServerError)
return
}

w.Header().Set("Content-Type", "application/json")
json.NewEncoder(w).Encode(map[string]interface{}{"id": id, "message": "Пользователь создан"})
}

func (h *Handler) Login(w http.ResponseWriter, r *http.Request) {
var req service.LoginRequest
if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
http.Error(w, err.Error(), http.StatusBadRequest)
return
}

user, err := h.userService.GetByUsername(req.Username)
if err != nil {
http.Error(w, "Неверный логин или пароль", http.StatusUnauthorized)
return
}

if !h.userService.VerifyPassword(user.PasswordHash, req.Password) {
http.Error(w, "Неверный логин или пароль", http.StatusUnauthorized)
return
}

// Проверка 2FA
if user.TwoFactorEnabled {
if req.TOTPCode == "" || !h.authService.VerifyTOTP(user.TwoFactorSecret, req.TOTPCode) {
http.Error(w, "Требуется код 2FA", http.StatusUnauthorized)
return
}
}

accessToken, refreshToken, err := h.authService.GenerateTokens(user.ID, user.Username)
if err != nil {
http.Error(w, err.Error(), http.StatusInternalServerError)
return
}

h.userService.SetOnlineStatus(user.ID, true)

w.Header().Set("Content-Type", "application/json")
json.NewEncoder(w).Encode(map[string]interface{}{
"access_token":  accessToken,
"refresh_token": refreshToken,
"user":          user,
})
}

func (h *Handler) Logout(w http.ResponseWriter, r *http.Request) {
// Получаем userID из токена
userID, _ := getUserIDFromToken(r, h.authService)
if userID > 0 {
h.userService.SetOnlineStatus(userID, false)
}
w.WriteHeader(http.StatusOK)
}

func (h *Handler) RefreshToken(w http.ResponseWriter, r *http.Request) {
var req struct {
RefreshToken string `json:"refresh_token"`
}
if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
http.Error(w, err.Error(), http.StatusBadRequest)
return
}

accessToken, refreshToken, err := h.authService.RefreshToken(req.RefreshToken)
if err != nil {
http.Error(w, err.Error(), http.StatusUnauthorized)
return
}

w.Header().Set("Content-Type", "application/json")
json.NewEncoder(w).Encode(map[string]interface{}{
"access_token":  accessToken,
"refresh_token": refreshToken,
})
}

func (h *Handler) Enable2FA(w http.ResponseWriter, r *http.Request) {
userID, _ := getUserIDFromToken(r, h.authService)
if userID == 0 {
http.Error(w, "Unauthorized", http.StatusUnauthorized)
return
}

secret, err := h.authService.GenerateTOTPSecret()
if err != nil {
http.Error(w, err.Error(), http.StatusInternalServerError)
return
}

if err := h.userService.Enable2FA(userID, secret); err != nil {
http.Error(w, err.Error(), http.StatusInternalServerError)
return
}

user, _ := h.userService.GetByID(userID)
uri := h.authService.GetTOTPURI(secret, user.Username, "LocalMessenger")

w.Header().Set("Content-Type", "application/json")
json.NewEncoder(w).Encode(map[string]interface{}{
"secret": secret,
"uri":    uri,
})
}

func (h *Handler) Verify2FA(w http.ResponseWriter, r *http.Request) {
var req struct {
Code string `json:"code"`
}
if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
http.Error(w, err.Error(), http.StatusBadRequest)
return
}

userID, _ := getUserIDFromToken(r, h.authService)
user, err := h.userService.GetByID(userID)
if err != nil {
http.Error(w, err.Error(), http.StatusNotFound)
return
}

if !h.authService.VerifyTOTP(user.TwoFactorSecret, req.Code) {
http.Error(w, "Неверный код", http.StatusBadRequest)
return
}

w.Header().Set("Content-Type", "application/json")
json.NewEncoder(w).Encode(map[string]interface{}{"verified": true})
}

func (h *Handler) GetMe(w http.ResponseWriter, r *http.Request) {
userID, _ := getUserIDFromToken(r, h.authService)
if userID == 0 {
http.Error(w, "Unauthorized", http.StatusUnauthorized)
return
}

user, err := h.userService.GetByID(userID)
if err != nil {
http.Error(w, err.Error(), http.StatusNotFound)
return
}

w.Header().Set("Content-Type", "application/json")
json.NewEncoder(w).Encode(user)
}

func (h *Handler) UpdateUser(w http.ResponseWriter, r *http.Request) {
// Реализация обновления пользователя
w.WriteHeader(http.StatusOK)
}

func (h *Handler) GetUser(w http.ResponseWriter, r *http.Request) {
idStr := chi.URLParam(r, "id")
id, err := strconv.ParseInt(idStr, 10, 64)
if err != nil {
http.Error(w, err.Error(), http.StatusBadRequest)
return
}

user, err := h.userService.GetByID(id)
if err != nil {
http.Error(w, err.Error(), http.StatusNotFound)
return
}

w.Header().Set("Content-Type", "application/json")
json.NewEncoder(w).Encode(user)
}

func (h *Handler) SearchUsers(w http.ResponseWriter, r *http.Request) {
query := r.URL.Query().Get("q")
limit := 20

users, err := h.userService.Search(query, limit)
if err != nil {
http.Error(w, err.Error(), http.StatusInternalServerError)
return
}

w.Header().Set("Content-Type", "application/json")
json.NewEncoder(w).Encode(users)
}

func (h *Handler) GetSessions(w http.ResponseWriter, r *http.Request) {
// Реализация получения сессий
w.Header().Set("Content-Type", "application/json")
json.NewEncoder(w).Encode([]interface{}{})
}

func (h *Handler) DeleteSession(w http.ResponseWriter, r *http.Request) {
// Реализация удаления сессии
w.WriteHeader(http.StatusOK)
}

func (h *Handler) CreateChat(w http.ResponseWriter, r *http.Request) {
// Реализация создания чата
w.WriteHeader(http.StatusCreated)
}

func (h *Handler) GetChats(w http.ResponseWriter, r *http.Request) {
// Реализация получения списка чатов
w.Header().Set("Content-Type", "application/json")
json.NewEncoder(w).Encode([]interface{}{})
}

func (h *Handler) GetChat(w http.ResponseWriter, r *http.Request) {
// Реализация получения чата
w.WriteHeader(http.StatusOK)
}

func (h *Handler) UpdateChat(w http.ResponseWriter, r *http.Request) {
w.WriteHeader(http.StatusOK)
}

func (h *Handler) DeleteChat(w http.ResponseWriter, r *http.Request) {
w.WriteHeader(http.StatusOK)
}

func (h *Handler) AddMember(w http.ResponseWriter, r *http.Request) {
w.WriteHeader(http.StatusOK)
}

func (h *Handler) RemoveMember(w http.ResponseWriter, r *http.Request) {
w.WriteHeader(http.StatusOK)
}

func (h *Handler) GetMessages(w http.ResponseWriter, r *http.Request) {
idStr := chi.URLParam(r, "id")
chatID, err := strconv.ParseInt(idStr, 10, 64)
if err != nil {
http.Error(w, err.Error(), http.StatusBadRequest)
return
}

limit := 50
offset := 0
if l := r.URL.Query().Get("limit"); l != "" {
strconv.Atoi(l)
}
if o := r.URL.Query().Get("offset"); o != "" {
strconv.Atoi(o)
}

messages, err := h.messageService.GetByChatID(chatID, limit, offset)
if err != nil {
http.Error(w, err.Error(), http.StatusInternalServerError)
return
}

w.Header().Set("Content-Type", "application/json")
json.NewEncoder(w).Encode(messages)
}

func (h *Handler) SendMessage(w http.ResponseWriter, r *http.Request) {
idStr := chi.URLParam(r, "id")
chatID, err := strconv.ParseInt(idStr, 10, 64)
if err != nil {
http.Error(w, err.Error(), http.StatusBadRequest)
return
}

userID, _ := getUserIDFromToken(r, h.authService)

var req struct {
Content   string  `json:"content"`
Type      string  `json:"type"`
MediaID   *int64  `json:"media_id,omitempty"`
ReplyToID *int64  `json:"reply_to_id,omitempty"`
}
if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
http.Error(w, err.Error(), http.StatusBadRequest)
return
}

msg, err := h.messageService.Create(chatID, userID, req.Content, req.Type, req.MediaID, req.ReplyToID)
if err != nil {
http.Error(w, err.Error(), http.StatusInternalServerError)
return
}

// Отправка через WebSocket всем подключенным клиентам в чате
h.broadcastMessage(chatID, msg)

w.Header().Set("Content-Type", "application/json")
w.WriteHeader(http.StatusCreated)
json.NewEncoder(w).Encode(msg)
}

func (h *Handler) EditMessage(w http.ResponseWriter, r *http.Request) {
msgIDStr := chi.URLParam(r, "msg_id")
msgID, _ := strconv.ParseInt(msgIDStr, 10, 64)

var req struct {
Content string `json:"content"`
}
if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
http.Error(w, err.Error(), http.StatusBadRequest)
return
}

if err := h.messageService.Update(msgID, req.Content); err != nil {
http.Error(w, err.Error(), http.StatusInternalServerError)
return
}

w.WriteHeader(http.StatusOK)
}

func (h *Handler) DeleteMessage(w http.ResponseWriter, r *http.Request) {
msgIDStr := chi.URLParam(r, "msg_id")
msgID, _ := strconv.ParseInt(msgIDStr, 10, 64)

if err := h.messageService.Delete(msgID); err != nil {
http.Error(w, err.Error(), http.StatusInternalServerError)
return
}

w.WriteHeader(http.StatusOK)
}

func (h *Handler) MarkAsRead(w http.ResponseWriter, r *http.Request) {
msgIDStr := chi.URLParam(r, "msg_id")
msgID, _ := strconv.ParseInt(msgIDStr, 10, 64)
userID, _ := getUserIDFromToken(r, h.authService)

if err := h.messageService.MarkAsRead(msgID, userID); err != nil {
http.Error(w, err.Error(), http.StatusInternalServerError)
return
}

w.WriteHeader(http.StatusOK)
}

func (h *Handler) AddReaction(w http.ResponseWriter, r *http.Request) {
msgIDStr := chi.URLParam(r, "msg_id")
msgID, _ := strconv.ParseInt(msgIDStr, 10, 64)
userID, _ := getUserIDFromToken(r, h.authService)

var req struct {
Emoji string `json:"emoji"`
}
if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
http.Error(w, err.Error(), http.StatusBadRequest)
return
}

if err := h.messageService.AddReaction(msgID, userID, req.Emoji); err != nil {
http.Error(w, err.Error(), http.StatusInternalServerError)
return
}

w.WriteHeader(http.StatusOK)
}

func (h *Handler) ForwardMessage(w http.ResponseWriter, r *http.Request) {
// Реализация пересылки
w.WriteHeader(http.StatusOK)
}

func (h *Handler) ReplyToMessage(w http.ResponseWriter, r *http.Request) {
// Реализация ответа
w.WriteHeader(http.StatusOK)
}

func (h *Handler) UploadFile(w http.ResponseWriter, r *http.Request) {
userID, _ := getUserIDFromToken(r, h.authService)

file, header, err := r.FormFile("file")
if err != nil {
http.Error(w, err.Error(), http.StatusBadRequest)
return
}
defer file.Close()

fileType := r.FormValue("type")
if fileType == "" {
fileType = "document"
}

fileInfo, err := h.fileService.Upload(userID, fileType, header.Filename, header.Header.Get("Content-Type"), file, header.Size)
if err != nil {
http.Error(w, err.Error(), http.StatusInternalServerError)
return
}

w.Header().Set("Content-Type", "application/json")
w.WriteHeader(http.StatusCreated)
json.NewEncoder(w).Encode(fileInfo)
}

func (h *Handler) GetFile(w http.ResponseWriter, r *http.Request) {
fileID := chi.URLParam(r, "file_id")

url, err := h.fileService.GetPresignedURL(fileID, time.Hour)
if err != nil {
http.Error(w, err.Error(), http.StatusNotFound)
return
}

w.Header().Set("Content-Type", "application/json")
json.NewEncoder(w).Encode(map[string]string{"url": url})
}

func (h *Handler) Search(w http.ResponseWriter, r *http.Request) {
query := r.URL.Query().Get("q")

messages, err := h.messageService.Search(query, nil, nil, nil, nil, nil, 50, 0)
if err != nil {
http.Error(w, err.Error(), http.StatusInternalServerError)
return
}

w.Header().Set("Content-Type", "application/json")
json.NewEncoder(w).Encode(messages)
}

func (h *Handler) AdminCreateUser(w http.ResponseWriter, r *http.Request) {
// Административное создание пользователя
w.WriteHeader(http.StatusCreated)
}

func (h *Handler) AdminDeleteUser(w http.ResponseWriter, r *http.Request) {
w.WriteHeader(http.StatusOK)
}

func (h *Handler) AdminGetLogs(w http.ResponseWriter, r *http.Request) {
w.Header().Set("Content-Type", "application/json")
json.NewEncoder(w).Encode([]interface{}{})
}

func (h *Handler) AdminBackup(w http.ResponseWriter, r *http.Request) {
w.WriteHeader(http.StatusOK)
}

func (h *Handler) WebSocketHandler(w http.ResponseWriter, r *http.Request) {
conn, err := upgrader.Upgrade(w, r, nil)
if err != nil {
return
}

// Аутентификация WebSocket подключения
userID, _ := getUserIDFromToken(r, h.authService)
if userID == 0 {
conn.Close()
return
}

h.wsClients[userID] = conn
defer func() {
delete(h.wsClients, userID)
conn.Close()
}()

for {
_, _, err := conn.ReadMessage()
if err != nil {
break
}
}
}

func (h *Handler) broadcastMessage(chatID int64, msg interface{}) {
for _, conn := range h.wsClients {
conn.WriteJSON(msg)
}
}

func getUserIDFromToken(r *http.Request, authService *service.AuthService) (int64, error) {
token := r.Header.Get("Authorization")
if token == "" {
return 0, nil
}

claims, err := authService.ValidateToken(token)
if err != nil {
return 0, err
}

return claims.UserID, nil
}
