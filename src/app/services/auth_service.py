import datetime
import uuid
from typing import Dict, Optional

import jwt
from decouple import config
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.app.db.models import UserModel


class User(BaseModel):
    """Модель пользователя для сервиса авторизации."""

    user_id: uuid.UUID
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    account: float

    class Config:
        """Конфиг для юзера."""

        from_attributes = True


SECRET_KEY = config('SECRET_KEY')
ALGORITHM = 'HS256'
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/login')

# Словарь для хранения активных токенов
active_tokens: Dict[str, User] = {}


class AuthService:
    """Сервис для управления авторизацией и пользователями."""

    def __init__(self, db: AsyncSession):
        """Инициализация сервиса авторизации с подключением к базе данных."""
        self.db = db

    async def register(
        self,
        username: str,
        password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> Optional[str]:
        """Регистрация нового пользователя."""
        async with self.db as session:
            query = select(UserModel).filter(UserModel.username == username)
            execution_result = await session.execute(query)
            existing_user = execution_result.scalar_one_or_none()

            if existing_user:
                return None

            user_id = uuid.uuid4()
            token = self._generate_token(username, user_id)

            new_user = UserModel(
                user_id=user_id,
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                account=0.0,
            )

            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)

            active_tokens[token] = User.from_orm(new_user)

            return token

    async def authenticate(self, username: str, password: str) -> Optional[str]:
        """Аутентификация пользователя."""
        async with self.db as session:
            query = select(UserModel).filter(UserModel.username == username)
            execution_result = await session.execute(query)
            user = execution_result.scalar_one_or_none()

            if not user or user.password != password:
                return None

            token = self._generate_token(username, user.user_id)

            active_tokens[token] = User.from_orm(user)

            return token

    async def verify_token(self, token: str) -> Optional[User]:
        """Верификация токена и получение пользователя."""
        if token in active_tokens:
            return active_tokens[token]

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except jwt.PyJWTError:
            return None

        user_id = payload.get('user_id')
        if not user_id:
            return None

        async with self.db as session:
            query = select(UserModel).filter(UserModel.user_id == user_id)
            execution_result = await session.execute(query)
            user_model = execution_result.scalar_one_or_none()
            if user_model:
                user = User.from_orm(user_model)
                active_tokens[token] = user
                return user
            return None

    def _generate_token(self, username: str, user_id: uuid.UUID) -> str:
        """Генерация JWT токена для пользователя."""
        payload = {
            'username': username,
            'user_id': str(user_id),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1),
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    async def update_user_balance(self, user_id: str, amount: float) -> bool:
        """Обновление баланса пользователя."""
        async with self.db as session:
            query = update(UserModel).where(UserModel.user_id == user_id).values(account=amount)
            execution_result = await session.execute(query)
            await session.commit()
            return execution_result.rowcount > 0

    async def get_user_balance(self, user_id: str) -> Optional[float]:
        """Получение баланса пользователя."""
        async with self.db as session:
            query = select(UserModel).filter(UserModel.user_id == user_id)
            execution_result = await session.execute(query)
            user = execution_result.scalar_one_or_none()
            return user.account if user else None
