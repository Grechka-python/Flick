"""
Модуль безопасности: аутентификация, авторизация, хеширование паролей, TOTP.
"""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

import pyotp
from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings


# === Password Hashing ===

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Хеширование пароля"""
    return pwd_context.hash(password)


# === JWT Tokens ===

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Создание access токена"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Создание refresh токена"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Декодирование токена"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def verify_access_token(token: str) -> Optional[dict]:
    """Проверка access токена"""
    payload = decode_token(token)
    if payload and payload.get("type") == "access":
        return payload
    return None


# === TOTP (2FA) ===

def generate_totp_secret() -> str:
    """Генерация секрета для TOTP"""
    return pyotp.random_base32()


def get_totp_uri(secret: str, username: str) -> str:
    """Получение URI для настройки TOTP в приложении-аутентификаторе"""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(
        name=username,
        issuer_name=settings.TOTP_ISSUER
    )


def verify_totp_code(secret: str, code: str) -> bool:
    """Проверка TOTP кода"""
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)


# === Security Utilities ===

def generate_secure_token(length: int = 32) -> str:
    """Генерация криптографически безопасного токена"""
    return secrets.token_urlsafe(length)


def hash_token(token: str) -> str:
    """Хеширование токена для хранения в БД"""
    return hashlib.sha256(token.encode()).hexdigest()


def verify_token_hash(token: str, token_hash: str) -> bool:
    """Проверка токена по хешу"""
    return hmac.compare_digest(hash_token(token), token_hash)


# === Authentication Helper ===

class AuthenticationError(Exception):
    """Ошибка аутентификации"""
    pass


class TokenExpiredError(AuthenticationError):
    """Токен истёк"""
    pass


class InvalidTokenError(AuthenticationError):
    """Неверный токен"""
    pass


def get_current_user_from_token(token: str) -> dict:
    """Получение данных пользователя из токена"""
    payload = verify_access_token(token)
    if not payload:
        raise InvalidTokenError("Invalid token")

    user_id = payload.get("sub")
    if not user_id:
        raise InvalidTokenError("Invalid token payload")

    return {"user_id": UUID(user_id), "username": payload.get("username")}
