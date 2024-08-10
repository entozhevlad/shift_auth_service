


import logging
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from src.app.services.auth_service import AuthService, oauth2_scheme

logging.basicConfig(level=logging.INFO)

app = FastAPI()
auth_service = AuthService()

def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    user = auth_service.verify_token(token)
    if user is None:
        raise HTTPException(
            status_code=401, detail="Invalid or expired token"
        )
    return user

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
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    token = auth_service.authenticate(form_data.username, form_data.password)
    if not token:
        raise HTTPException(status_code=400, detail="Invalid username or password")
    return {"access_token": token, "token_type": "bearer"}

@app.post("/verify")
async def verify(current_user: str = Depends(get_current_user)):
    return {"user": current_user}
