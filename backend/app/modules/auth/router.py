from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db   # confirm this is the actual name/path in your session.py
from app.modules.auth.schemas import UserCreate, UserResponse
from app.modules.auth.service import register_user, EmailAlreadyExistsError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        new_user = await register_user(db, user_data)
    except EmailAlreadyExistsError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    return new_user