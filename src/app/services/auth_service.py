import datetime
from dataclasses import dataclass
from typing import Dict, Optional

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from decouple import config

SECRET_KEY = config('SECRET_KEY')
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@dataclass
class User:
    username: str
    password: str
    token: Optional[str] = None

class AuthService:
    def __init__(self):
        self.users: Dict[str, User] = {}

    def register(self, username: str, password: str) -> Optional[str]:
        if username in self.users:
            return None
        token = self._generate_token(username)
        user = User(username=username, password=password, token=token)
        self.users[username] = user
        return token

    def authenticate(self, username: str, password: str) -> Optional[str]:
        user = self.users.get(username)
        if not user or user.password != password:
            return None
        user.token = self._generate_token(username)
        return user.token

    def _generate_token(self, username: str) -> str:
        payload = {
            "username": username,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    def verify_token(self, token: str) -> Optional[str]:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("username")
            if username is None:
                return None
            return username
        except jwt.PyJWTError:
            return None

def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    auth_service = AuthService()  # Создаем новый экземпляр AuthService
    user = auth_service.verify_token(token)
    if user is None:
        raise HTTPException(
            status_code=401, detail="Invalid or expired token"
        )
    return user
