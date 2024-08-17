import datetime
import uuid
from typing import Optional

import jwt
from decouple import config
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.app.db.models import UserModel
from src.app.db.db import get_db
from pydantic import BaseModel


class User(BaseModel):
    user_id: uuid.UUID
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    account: float


SECRET_KEY = config('SECRET_KEY')
ALGORITHM = 'HS256'
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/login')


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

            return token

    async def authenticate(self, username: str, password: str) -> Optional[str]:
        async with self.db as session:
            query = select(UserModel).filter(UserModel.username == username)
            result = await session.execute(query)
            user = result.scalar_one_or_none()

            if not user or user.password != password:
                return None

            user.token = self._generate_token(username, user.user_id)
            return user.token

    async def verify_token(self, token: str) -> Optional[UserModel]:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except jwt.PyJWTError:
            return None

        username = payload.get('username')
        user_id = payload.get('user_id')

        if not username or not user_id:
            return None

        async with self.db as session:
            query = select(UserModel).filter(UserModel.username == username)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    def _generate_token(self, username: str, user_id: uuid.UUID) -> str:
        payload = {
            'username': username,
            'user_id': str(user_id),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1),
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
