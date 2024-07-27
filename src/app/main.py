import logging
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordRequestForm
from src.app.services.auth_service import AuthService

app = FastAPI()
logging.basicConfig(level=logging.INFO)

auth_service = AuthService()


class RegisterUser(BaseModel):
    username: str
    password: str


@app.post("/register")
def register(user: RegisterUser):
    token = auth_service.register(user.username, user.password)
    if token:
        return {"token": token}
    raise HTTPException(status_code=400, detail="User already exists")


@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    token = auth_service.authenticate(form_data.username, form_data.password)
    if token:
        return {"token": token}
    raise HTTPException(status_code=400, detail="Invalid username or password")
