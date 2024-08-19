import datetime
import uuid
from typing import Optional, Dict

import jwt
from decouple import config
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update

from src.app.db.models import UserModel
from pydantic import BaseModel


class User(BaseModel):
    user_id: uuid.UUID
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    account: float

    class Config:
        from_attributes = True


SECRET_KEY = config('SECRET_KEY')
ALGORITHM = 'HS256'
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/login')

# Словарь для хранения активных токенов
active_tokens: Dict[str, User] = {}


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(
        self,
        username: str,
        password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> Optional[str]:
        async with self.db as session:
            query = select(UserModel).filter(UserModel.username == username)
            result = await session.execute(query)
            existing_user = result.scalar_one_or_none()

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
                account=0.0
            )

            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)

            # Сохраняем токен и пользователя в локальный словарь
            active_tokens[token] = User.from_orm(new_user)

            return token

    async def authenticate(self, username: str, password: str) -> Optional[str]:
        async with self.db as session:
            query = select(UserModel).filter(UserModel.username == username)
            result = await session.execute(query)
            user = result.scalar_one_or_none()

            if not user or user.password != password:
                return None

            token = self._generate_token(username, user.user_id)

            # Сохраняем токен и пользователя в локальный словарь
            active_tokens[token] = User.from_orm(user)

            return token

    async def verify_token(self, token: str) -> Optional[User]:
        # Проверяем наличие токена в локальном словаре
        if token in active_tokens:
            return active_tokens[token]

        # Если токен не найден, декодируем и проверяем его валидность
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except jwt.PyJWTError:
            return None

        user_id = payload.get('user_id')
        if not user_id:
            return None

        async with self.db as session:
            query = select(UserModel).filter(UserModel.user_id == user_id)
            result = await session.execute(query)
            user_model = result.scalar_one_or_none()
            if user_model:
                user = User.from_orm(user_model)
                # Сохраняем токен в локальный словарь, если он валиден
                active_tokens[token] = user
                return user
            return None

    def _generate_token(self, username: str, user_id: uuid.UUID) -> str:
        payload = {
            'username': username,
            'user_id': str(user_id),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1),
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    async def update_user_balance(self, user_id: str, amount: float) -> bool:
        async with self.db as session:
            query = update(UserModel).where(UserModel.user_id ==
                                            user_id).values(account=amount)
            result = await session.execute(query)
            await session.commit()
            return result.rowcount > 0

    async def get_user_balance(self, user_id: str) -> Optional[float]:
        async with self.db as session:
            query = select(UserModel).filter(UserModel.user_id == user_id)
            result = await session.execute(query)
            user = result.scalar_one_or_none()
            return user.account if user else None
