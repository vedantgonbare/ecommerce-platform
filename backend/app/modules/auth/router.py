from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db   # confirm this is the actual name/path in your session.py
from app.modules.auth.schemas import UserCreate, UserResponse
from app.modules.auth.service import register_user, EmailAlreadyExistsError
from app.modules.auth.schemas import UserCreate, UserResponse, UserLogin, Token
from app.modules.auth.service import (
    register_user,
    EmailAlreadyExistsError,
    authenticate_user,
    InvalidCredentialsError,
)
from app.modules.auth.security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        new_user = await register_user(db, user_data)
    except EmailAlreadyExistsError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    return new_user

@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    try:
        user = await authenticate_user(db, credentials.email, credentials.password)
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = create_access_token(str(user.id))
    return Token(access_token=access_token)