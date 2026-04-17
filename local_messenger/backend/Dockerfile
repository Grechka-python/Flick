FROM golang:1.21-alpine

WORKDIR /app

# Установка зависимостей
RUN apk add --no-cache git

# Копирование go.mod и go.sum
COPY go.mod ./
RUN go mod download || true

# Копирование исходного кода
COPY . .

# Сборка приложения
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o main ./cmd/server.go

# Экспозиция порта
EXPOSE 8080

# Запуск приложения
CMD ["./main"]
