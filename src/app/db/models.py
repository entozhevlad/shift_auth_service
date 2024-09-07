from sqlalchemy import Column, String, Float, UUID
from src.app.db.db import Base


class UserModel(Base):
    __tablename__ = 'users'

    user_id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    account = Column(Float, default=0.0)

