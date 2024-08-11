import logging
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Dict, Optional
from src.app.services.auth_service import AuthService, oauth2_scheme

logging.basicConfig(level=logging.INFO)

app = FastAPI()
auth_service = AuthService()

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Получает текущего пользователя из токена."""
    user = auth_service.verify_token(token)
    if user is None:
        raise HTTPException(
            status_code=401, detail="Invalid or expired token"
        )
    return user

class UserCredentials(BaseModel):
    username: str
    password: str
    first_name: Optional[str] = None  # Добавлено для регистрации
    last_name: Optional[str] = None   # Добавлено для регистрации

@app.post("/register")
async def register(user_credentials: UserCredentials):
    """Регистрирует нового пользователя."""
    # Регистрация теперь требует имени и фамилии
    token = auth_service.register(
        user_credentials.username,
        user_credentials.password,
        user_credentials.first_name,
        user_credentials.last_name,
    )
    if not token:
        raise HTTPException(status_code=400, detail="Пользователь уже существует")
    return {"token": token}

@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Аутентифицирует пользователя и возвращает токен."""
    token = auth_service.authenticate(form_data.username, form_data.password)
    if not token:
        raise HTTPException(status_code=400, detail="Неправильное имя пользователя или пароль")
    return {"access_token": token, "token_type": "bearer"}

@app.post("/verify")
async def verify(current_user: dict = Depends(get_current_user)):
    """Проверяет валидность токена и возвращает информацию о пользователе."""
    return {"user": current_user}

@app.get("/healthz/ready")
async def health_check():
    """Проверка состояния сервиса."""
    return {"status": "healthy"}
