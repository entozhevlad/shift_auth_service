import logging
import shutil
from typing import Optional
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, Header, status, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from src.app.db.db import get_db
from src.app.external.kafka.kafka import KafkaProducerService
from src.app.services.auth_service import AuthService, User


logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Глобальный экземпляр AuthService
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/login')


def get_auth_service(db: AsyncSession = Depends(get_db)):
    return AuthService(db)


async def get_auth_header(token: str = Depends(oauth2_scheme)):
    return {"Authorization": f"Bearer {token}"}

# Глобальная зависимость для OAuth2


# Глобальный экземпляр AuthService, созданный с использованием зависимости
auth_service_dependency = Depends(get_auth_service)

# Получаем текущего пользователя


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    user = await auth_service.verify_token(token)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Неверный или истекший токен",
        )
    return user


@app.post('/register')
async def register(
    username: str,
    password: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Регистрирует нового пользователя."""
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
    auth_service: AuthService = Depends(get_auth_service)
):
    """Аутентифицирует пользователя и возвращает токен."""
    token = await auth_service.authenticate(
        form_data.username,
        form_data.password,
    )
    if not token:
        raise HTTPException(
            status_code=400,
            detail="Неправильное имя пользователя или пароль",
        )
    return {"access_token": token, "token_type": "bearer"}


@app.get('/healthz/ready')
async def health_check():
    return {"status": "healthy"}


@app.post('/verify')
async def verify(
    current_user: User = Depends(get_current_user),
    photo: UploadFile = File(...),
):
    """Метод верификации пользователя с сохранением фотографии и отправкой сообщения."""
    user_id = current_user.user_id
    photo_path = f'/app/photos/{user_id}_{photo.filename}'

    with open(photo_path, 'wb') as buffer:
        shutil.copyfileobj(photo.file, buffer)

    kafka_producer = KafkaProducerService()
    kafka_producer.send_message(
        topic='face_verification',
        key=str(user_id),
        value={'user_id': str(user_id), 'photo_path': photo_path},
    )

    return {'status': 'photo accepted for processing'}


@app.get('/users/balance')
async def get_user_balance(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Получает информацию о балансе пользователя."""
    user_id = current_user.user_id
    balance = await auth_service.get_user_balance(user_id)
    if balance is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"balance": balance}


@app.patch('/users/update_balance')
async def update_user_balance(
    new_balance: float,
    token: str = Query(..., alias="Authorization"),
    auth_service: AuthService = Depends(get_auth_service)
):
    if not token:
        logger.error("Token missing")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing"
        )

    token = token.replace("Bearer ", "")
    if not token:
        logger.error("Token missing in Authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing in Authorization header"
        )

    user = await auth_service.verify_token(token)
    if not user:
        logger.error("Invalid or expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    user_id = user.user_id  # Извлечение user_id из данных токена

    success = await auth_service.update_user_balance(user_id, new_balance)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")

    logger.info(f"User {user_id} balance updated to {new_balance}")
    return {"status": "balance updated"}
