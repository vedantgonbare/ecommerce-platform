from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
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

@router.post("/login")
async def login(credentials: UserLogin, response: Response, db: AsyncSession = Depends(get_db)):
    try:
        user = await authenticate_user(db, credentials.email, credentials.password)
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 30,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
    )

    return {"message": "Login successful"}

@router.get("/me", response_model=UserResponse)
async def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/refresh")
async def refresh(request: Request, response: Response):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
    )

    refresh_token = request.cookies.get("refresh_token")
    if refresh_token is None:
        raise credentials_exception

    try:
        payload = jwt.decode(refresh_token, settings.jwt_secret_key, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise credentials_exception
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except (JWTError, ValueError):
        raise credentials_exception

    new_access_token = create_access_token(user_id)

    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 30,
    )

    return {"message": "Token refreshed"}