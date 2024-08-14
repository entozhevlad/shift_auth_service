import logging
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordRequestForm
from typing import Optional
from src.app.services.auth_service import AuthService, oauth2_scheme, User

logging.basicConfig(level=logging.INFO)

app = FastAPI()
auth_service = AuthService()

def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Получает текущего пользователя из токена."""
    user = auth_service.verify_token(token)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user

@app.post("/register")
async def register(username: str, password: str, first_name: Optional[str] = None, last_name: Optional[str] = None):
    """Регистрирует нового пользователя."""
    token = auth_service.register(
        username,
        password,
        first_name,
        last_name,
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
async def verify(current_user: User = Depends(get_current_user)):
    """Проверяет валидность токена и возвращает информацию о пользователе."""
    return {"user": {
        "username": current_user.username,
        "user_id": str(current_user.user_id),
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "account": current_user.account
    }}

@app.get("/healthz/ready")
async def health_check():
    """Проверка состояния сервиса."""
    return {"status": "healthy"}

# @app.get("/verify_by_token")
# async def verify_by_token(token: str = Query(...)):
#     """Проверяет валидность токена и возвращает информацию о пользователе."""
#     user = auth_service.verify_token(token)
#     if user is None:
#         raise HTTPException(status_code=401, detail="Invalid or expired token")
#     return {
#         "username": user.username,
#         "user_id": str(user.user_id),
#         "first_name": user.first_name,
#         "last_name": user.last_name,
#         "account": user.account
#     }
