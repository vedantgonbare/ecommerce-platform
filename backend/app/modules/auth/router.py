from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db   
from app.modules.auth.schemas import UserCreate, UserResponse
from app.modules.auth.service import register_user, EmailAlreadyExistsError
from app.modules.auth.schemas import UserCreate, UserResponse, UserLogin, Token, RefreshRequest
from app.modules.auth.service import (
    register_user,
    EmailAlreadyExistsError,
    authenticate_user,
    InvalidCredentialsError,
)
from app.modules.auth.security import create_access_token
from app.modules.users.models import User
from app.modules.auth.dependencies import get_current_user
from jose import jwt, JWTError
from app.modules.auth.security import create_access_token, create_refresh_token, ALGORITHM
from app.core.config import settings

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
    refresh_token = create_refresh_token(str(user.id))
    return Token(access_token=access_token, refresh_token=refresh_token)

@router.get("/me", response_model=UserResponse)
async def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/refresh", response_model=Token)
async def refresh(request: RefreshRequest):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
    )
    try:
        payload = jwt.decode(request.refresh_token, settings.jwt_secret_key, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise credentials_exception
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except (JWTError, ValueError):
        raise credentials_exception

    new_access_token = create_access_token(user_id)
    return Token(access_token=new_access_token)