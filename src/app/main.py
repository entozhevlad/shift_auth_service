import logging
import shutil
import time
from typing import Optional

import redis.asyncio as redis
from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, Response, UploadFile
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.db.db import get_db
from src.app.external.kafka.kafka import KafkaProducerService
from src.app.services.auth_service import AuthService, User

logging.basicConfig(level=logging.INFO)

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/login')


def get_auth_service(db: AsyncSession = Depends(get_db)):
    """Инициализация сервиса авторизации."""
    return AuthService(db)


async def get_auth_header(token: str = Depends(oauth2_scheme)):
    """Метод получения auth_header."""
    return {'Authorization': f'Bearer {token}'}


resource = Resource.create(attributes={'service.name': 'auth_service'})
trace_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(trace_provider)

jaeger_exporter = JaegerExporter(
    agent_host_name='jaeger',  # Jaeger host из docker-compose
    agent_port=6831,  # порт Jaeger для UDP
)

span_processor = BatchSpanProcessor(jaeger_exporter)
trace_provider.add_span_processor(span_processor)

FastAPIInstrumentor.instrument_app(app)
RequestsInstrumentor().instrument()


async def get_redis():
    """Инициализация Redis."""
    return redis.Redis(host='redis', port=6379, db=0, decode_responses=True)


@app.on_event('shutdown')
def shutdown_tracer():
    """Завершение работы (shutdown) при завершении приложения."""
    try:
        trace.get_tracer_provider().shutdown()
    except Exception as exc:
        return f'Ошибка завершения трейсера: {exc}'


REQUEST_COUNT = Counter(
    'request_count', 'Total request count',
    ['endpoint', 'http_status'],
)
REQUEST_DURATION = Histogram(
    'request_duration_seconds', 'Duration of requests in seconds', ['endpoint'],
)
AUTH_SUCCESS = Counter('auth_success_total', 'Total successful authentication attempts')
AUTH_FAILURE = Counter('auth_failure_total', 'Total failed authentication attempts')


@app.middleware('http')
async def metrics_middleware(request: Request, call_next):
    """Миддлвари для метрик."""
    start_time = time.time()
    response = await call_next(request)
    request_duration = time.time() - start_time

    REQUEST_COUNT.labels(
        endpoint=request.url.path,
        http_status=response.status_code,
    ).inc()

    REQUEST_DURATION.labels(endpoint=request.url.path).observe(request_duration)

    return response


@app.get('/metrics')
async def get_metrics():
    """Ручка получения метрик."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
    redis_client: redis.Redis = Depends(get_redis),
) -> User:
    """Ручка получения пользователя."""
    user_data = await redis_client.get(f'user:{token}')
    if user_data:
        return User.parse_raw(user_data)

    user = await auth_service.verify_token(token)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail='Неверный или истекший токен',
        )

    await redis_client.set(f'user:{token}', user.json(), ex=3600)
    return user


@app.post('/register')
async def register(
    username: str,
    password: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Регистрирует нового пользователя."""
    token = await auth_service.register(
        username, password, first_name, last_name,
    )
    if not token:
        raise HTTPException(
            status_code=400,
            detail='Пользователь уже существует',
        )
    return {'token': token}


@app.post('/login')
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Аутентифицирует пользователя и возвращает токен."""
    token = await auth_service.authenticate(
        form_data.username, form_data.password,
    )
    if not token:
        AUTH_FAILURE.inc()
        raise HTTPException(
            status_code=400,
            detail='Неправильное имя пользователя или пароль',
        )

    AUTH_SUCCESS.inc()
    return {'access_token': token, 'token_type': 'bearer'}


@app.get('/healthz/ready')
async def health_check():
    """Ручка проверки доступности сервиса."""
    return {'status': 'healthy'}


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
        message_data={'user_id': str(user_id), 'photo_path': photo_path},
    )

    return {'status': 'photo accepted for processing'}


@app.get('/users/balance')
async def get_user_balance(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Получает баланс пользователя."""
    balance = await auth_service.get_user_balance(current_user.user_id)
    return {'balance': balance}


@app.patch('/users/update_balance')
async def update_user_balance(
    amount: float = Query(...),
    token: str = Query(..., alias='Authorization'),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Обновление баланса пользователя."""
    if not token:
        raise HTTPException(
            status_code=401,
            detail='Token missing',
        )

    token = token.replace('Bearer ', '')
    if not token:
        raise HTTPException(
            status_code=401,
            detail='Token missing in Authorization header',
        )

    user = await auth_service.verify_token(token)
    if not user:
        raise HTTPException(
            status_code=401,
            detail='Invalid or expired token',
        )

    user_id = user.user_id

    success = await auth_service.update_user_balance(user_id, amount)
    if not success:
        raise HTTPException(status_code=404, detail='User not found')

    return {'status': 'balance updated'}
