from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from decouple import config
from sqlalchemy import MetaData



DATABASE_URL = config(
    'DATABASE_URL', default='postgresql+asyncpg://postgres:postgres@db:5432/auth_db')

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()
metadata = MetaData()



async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

