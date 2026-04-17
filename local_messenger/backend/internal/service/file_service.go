package service

import (
"context"
"fmt"
"io"
"time"

"github.com/minio/minio-go/v7"
"github.com/minio/minio-go/v7/pkg/credentials"
)

type FileService struct {
client *minio.Client
bucket string
}

func NewFileService(endpoint, accessKey, secretKey string) *FileService {
client, err := minio.New(endpoint, &minio.Options{
Creds:  credentials.NewStaticV4(accessKey, secretKey, ""),
Secure: false,
})
if err != nil {
panic(err)
}

ctx := context.Background()
bucketName := "local-messenger"

// Создаём бакет если не существует
err = client.MakeBucket(ctx, bucketName, minio.MakeBucketOptions{})
if err != nil {
exists, _ := client.BucketExists(ctx, bucketName)
if !exists {
panic(err)
}
}

return &FileService{
client: client,
bucket: bucketName,
}
}

type FileInfo struct {
ID        int64     `json:"id"`
UserID    int64     `json:"user_id"`
FileType  string    `json:"file_type"`
MimeType  string    `json:"mime_type"`
FileName  string    `json:"file_name"`
FileSize  int64     `json:"file_size"`
FilePath  string    `json:"file_path"`
CreatedAt time.Time `json:"created_at"`
}

func (s *FileService) Upload(userID int64, fileType, fileName, mimeType string, reader io.Reader, fileSize int64) (*FileInfo, error) {
ctx := context.Background()

// Генерируем уникальный путь
filePath := fmt.Sprintf("users/%d/%s/%s", userID, time.Now().Format("2006/01/02"), fileName)

// Загружаем в MinIO
_, err := s.client.PutObject(ctx, s.bucket, filePath, reader, fileSize, minio.PutObjectOptions{
ContentType: mimeType,
})
if err != nil {
return nil, err
}

return &FileInfo{
UserID:   userID,
FileType: fileType,
FileName: fileName,
MimeType: mimeType,
FileSize: fileSize,
FilePath: filePath,
}, nil
}

func (s *FileService) Get(filePath string) (*minio.Object, error) {
ctx := context.Background()
return s.client.GetObject(ctx, s.bucket, filePath, minio.GetObjectOptions{})
}

func (s *FileService) GetPresignedURL(filePath string, expiry time.Duration) (string, error) {
ctx := context.Background()
return s.client.PresignedGetObject(ctx, s.bucket, filePath, expiry, nil)
}

func (s *FileService) Delete(filePath string) error {
ctx := context.Background()
return s.client.RemoveObject(ctx, s.bucket, filePath, minio.RemoveObjectOptions{})
}
