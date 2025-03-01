from services.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db import get_db
from pydantic import BaseModel, EmailStr
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter
from slowapi.util import get_remote_address
from datetime import datetime, timedelta
from typing import Optional
import jwt
from config import get_settings
import os
from models.user import User

router = APIRouter()
settings = get_settings()
limiter = Limiter(key_func=get_remote_address)

# Add these to your environment variables
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str

async def get_user(email: str, db: AsyncSession):
    result = await db.execute(
        select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()

@router.post("/register")
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    # Check if user already exists
    existing_user = await get_user(user_data.email, db)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username is taken
    result = await db.execute(
        select(User).where(User.username == user_data.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new user
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=User.hash_password(user_data.password)
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return {"message": "User created successfully"}
    

@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    user = await get_user(form_data.username, db)
    if not user or not user.verify_password(form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET, 
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

# Add this function to handle user authentication
async def authenticate_user(username: str, password: str):
    # Implement your user authentication logic here
    # This is just a placeholder - replace with your actual authentication
    if username == "test" and password == "test":  # Don't use this in production!
        return {"username": username}
    return None

@router.post("/logout")
async def logout(current_user: str = Depends(get_current_user)):
    # In a more complex system, you might want to invalidate the token here
    # For now, we'll just return a success message as the frontend handles the token removal
    return {"message": "Successfully logged out"}

