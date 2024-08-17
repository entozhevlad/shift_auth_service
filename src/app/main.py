import logging
import shutil
from typing import Optional

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.security import OAuth2PasswordRequestForm

from src.app.external.kafka.kafka import KafkaProducerService
from src.app.services.auth_service import AuthService, User, oauth2_scheme

logging.basicConfig(level=logging.INFO)

app = FastAPI()
auth_service = AuthService()

# Переменные для сложных значений по умолчанию
oauth2_scheme_dependency = Depends(oauth2_scheme)
oauth2_password_request_form_dependency = Depends(OAuth2PasswordRequestForm)


def get_current_user(token: str = oauth2_scheme_dependency) -> User:
    """Получает текущего пользователя из токена."""
    user = auth_service.verify_token(token)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail='Неверный или истекший токен',
        )
    return user


get_cur_user_dependancy = Depends(get_current_user)


@app.post('/register')
async def register(
    username: str,
    password: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
):
    """Регистрирует нового пользователя."""
    token = auth_service.register(
        username,
        password,
        first_name,
        last_name,
    )
    if not token:
        raise HTTPException(
            status_code=400,
            detail='Пользователь уже существует',
        )
    return {'token': token}


@app.post('/login')
async def login(
    form_data: OAuth2PasswordRequestForm = oauth2_password_request_form_dependency,
):
    """Аутентифицирует пользователя и возвращает токен."""
    token = auth_service.authenticate(
        form_data.username,
        form_data.password,
    )
    if not token:
        raise HTTPException(
            status_code=400,
            detail='Неправильное имя пользователя или пароль',
        )
    return {
        'access_token': token,
        'token_type': 'bearer',
    }


@app.get('/healthz/ready')
async def health_check():
    """Проверка состояния сервиса."""
    return {'status': 'healthy'}


@app.post('/verify')
async def verify(
    current_user: User = Depends(get_current_user),
    photo: UploadFile = File(...),
):
    """Метод верификации пользователя с сохранением фотографии и отправкой сообщения."""
    user_id = current_user.user_id
    photo_path = '/app/photos/{0}_{1}'.format(user_id, photo.filename)
    with open(photo_path, 'wb') as buffer:
        shutil.copyfileobj(photo.file, buffer)
    kafka_producer = KafkaProducerService()
    kafka_producer.send_message(
        topic='face_verification',
        key=str(user_id),
        value={'user_id': str(user_id), 'photo_path': photo_path},
    )
    return {'status': 'photo accepted for processing'}
