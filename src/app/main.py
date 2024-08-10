import logging
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from src.app.services.auth_service import AuthService, get_current_user

logging.basicConfig(level=logging.INFO)

app = FastAPI()
auth_service = AuthService()

class UserCredentials(BaseModel):
    username: str
    password: str

@app.post("/auth_service/register")
async def register(user_credentials: UserCredentials):
    token = auth_service.register(user_credentials.username, user_credentials.password)
    if not token:
        raise HTTPException(status_code=400, detail="User already exists")
    return {"token": token}

@app.post("/auth_service/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    token = auth_service.authenticate(form_data.username, form_data.password)
    if not token:
        raise HTTPException(status_code=400, detail="Invalid username or password")
    return {"access_token": token, "token_type": "bearer"}

@app.post("/auth_service/verify")
async def verify(current_user: str = Depends(get_current_user)):
    return {"user": current_user}
