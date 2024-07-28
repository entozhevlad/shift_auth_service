import logging
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from src.app.services.auth_service import AuthService, get_current_user

logging.basicConfig(level=logging.INFO)

app = FastAPI()
auth_service = AuthService()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class UserCredentials(BaseModel):
    username: str
    password: str


@app.post("/register")
async def register(user_credentials: UserCredentials):
    token = auth_service.register(user_credentials.username, user_credentials.password)
    if not token:
        raise HTTPException(status_code=400, detail="User already exists")
    return {"token": token}


@app.post("/login")
async def login(user_credentials: UserCredentials):
    token = auth_service.authenticate(
        user_credentials.username, user_credentials.password)
    if not token:
        raise HTTPException(status_code=400, detail="Invalid username or password")
    return {"token": token}


@app.post("/verify")
async def verify(token: str):
    user = auth_service.verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"user": user}
