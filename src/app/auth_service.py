# src/app/auth_service.py
import datetime
from dataclasses import dataclass
from typing import Dict, Optional

import jwt
from decouple import config

SECRET_KEY = config('SECRET_KEY')


@dataclass
class User:
    """Класс, представляющий пользователя с именем, паролем и токеном."""

    username: str
    password: str
    token: Optional[str] = None


class AuthService:
    """Сервис аутентификации пользователей с использованием JWT."""

    def __init__(self):
        """Конструктор класса."""
        self.users: Dict[str, User] = {}

    def register(self, username: str, password: str) -> Optional[str]:
        """Регистрирует нового пользователя. Возвращает JWT токен."""
        if username in self.users:
            return None
        token = self._generate_token(username)
        user = User(username=username, password=password, token=token)
        self.users[username] = user
        return token

    def authenticate(self, username: str, password: str) -> Optional[str]:
        """Аутентифицирует пользователя по имени и паролю."""
        user = self.users.get(username)
        if not user or user.password != password:
            return None
        user.token = self._generate_token(username)
        return user.token

    def _generate_token(self, username: str) -> str:
        """Генерирует JWT токен для указанного имени пользователя."""
        payload = {
            'username': username,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1),
        }
        return jwt.encode(payload, SECRET_KEY, algorithm='HS256')
