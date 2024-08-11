import datetime
import uuid
from dataclasses import dataclass
from typing import Dict, Optional
import jwt
from fastapi.security import OAuth2PasswordBearer
from decouple import config

SECRET_KEY = config('SECRET_KEY')
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

@dataclass
class User:
    """Класс, представляющий пользователя."""
    username: str
    password: str
    user_id: uuid.UUID
    first_name: str
    last_name: str
    token: Optional[str] = None

class AuthService:
    def __init__(self):
        self.users: Dict[str, User] = {}

    def register(self, username: str, password: str, first_name: str, last_name: str) -> Optional[str]:
        """Регистрирует нового пользователя."""
        if username in self.users:
            return None
        user_id = uuid.uuid4()  # Генерируем уникальный идентификатор пользователя
        token = self._generate_token(username, user_id)
        user = User(username=username, password=password, user_id=user_id, first_name=first_name, last_name=last_name, token=token)
        self.users[username] = user
        return token

    def authenticate(self, username: str, password: str) -> Optional[str]:
        """Аутентифицирует пользователя."""
        user = self.users.get(username)
        if not user or user.password != password:
            return None
        user.token = self._generate_token(username, user.user_id)
        return user.token

    def _generate_token(self, username: str, user_id: uuid.UUID) -> str:
        """Создает JWT-токен."""
        payload = {
            "username": username,
            "user_id": str(user_id),  # Добавляем user_id в токен
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    def verify_token(self, token: str) -> Optional[User]:
        """Проверяет JWT-токен и извлекает полную информацию о пользователе."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("username")
            user_id: str = payload.get("user_id")
            if username is None or user_id is None:
                return None
            user = self.users.get(username)
            return user
        except jwt.PyJWTError:
            return None
