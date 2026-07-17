from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.modules.users.models import User
from app.modules.auth.security import hash_password
from app.modules.auth.schemas import UserCreate


class EmailAlreadyExistsError(Exception):
    pass


async def register_user(db: AsyncSession, user_data: UserCreate) -> User:
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise EmailAlreadyExistsError()

    hashed = hash_password(user_data.password)

    new_user = User(email=user_data.email, hashed_password=hashed)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user