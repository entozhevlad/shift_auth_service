import logging
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.db.db import get_db
from src.app.services.auth_service import AuthService, oauth2_scheme, User
from src.app.external.kafka.kafka import KafkaProducerService

logging.basicConfig(level=logging.INFO)

app = FastAPI()


def get_auth_service(db: AsyncSession = Depends(get_db)):
    return AuthService(db)


oauth2_scheme_dependency = Depends(oauth2_scheme)
auth_service_dependency = Depends(get_auth_service)


def get_current_user(
    token: str = oauth2_scheme_dependency,
    auth_service: AuthService = auth_service_dependency
) -> User:
    user = auth_service.verify_token(token)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Неверный или истекший токен",
        )
    return user


get_cur_user_dependency = Depends(get_current_user)


@app.post('/register')
async def register(
    username: str,
    password: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    auth_service: AuthService = auth_service_dependency
):
    token = await auth_service.register(
        username,
        password,
        first_name,
        last_name,
    )
    if not token:
        raise HTTPException(
            status_code=400,
            detail="Пользователь уже существует",
        )
    return {"token": token}


@app.post('/login')
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = auth_service_dependency
):
    token = await auth_service.authenticate(
        form_data.username,
        form_data.password,
    )
    if not token:
        raise HTTPException(
            status_code=400,
            detail="Неправильное имя пользователя или пароль",
        )
    return {"token": token,}


@app.get('/healthz/ready')
async def health_check():
    return {"status": "healthy"}


@app.post('/verify')
async def verify(
    current_user: User = get_cur_user_dependency,
    photo: UploadFile = File(...),
    auth_service: AuthService = auth_service_dependency
):
    user_id = current_user.user_id
    photo_path = f"/app/photos/{user_id}_{photo.filename}"
    with open(photo_path, "wb") as buffer:
        buffer.write(photo.file.read())

    kafka_producer = KafkaProducerService()
    kafka_producer.send_message(
        topic="face_verification",
        key=str(user_id),
        value={"user_id": str(user_id), "photo_path": photo_path},
    )

    return {"status": "photo accepted for processing"}

@app.get('/users/{user_id}/get_balance')
async def get_user_balance(
    user_id: str,
    auth_service: AuthService = auth_service_dependency
):
    user = await auth_service.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"balance": user.account}

@app.patch('/users/{user_id}/update_balance')
async def update_user_balance(
    user_id: str,
    new_balance: float,
    auth_service: AuthService = auth_service_dependency
):
    success = await auth_service.update_user_balance(user_id, new_balance)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "balance updated"}