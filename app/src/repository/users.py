from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from passlib.context import CryptContext
from app.src.database.models import User  
from app.src.schemas.users import UserCreate
from app.src.services.email import send_verification_email
from app.src.services.auth import create_access_token
from datetime import timedelta
from fastapi import HTTPException
import logging
from sqlalchemy import select
from app.src.database.models import User
from typing import Optional
from app.src.services.cloudinary_service import upload_avatar

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def get_user_by_email(email: str, db: AsyncSession) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()

async def create_user(user: UserCreate, db: AsyncSession) -> User:
    existing_user = await get_user_by_email(user.email, db)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    hashed_password = pwd_context.hash(user.password)
    db_user = User(email=user.email, password=hashed_password)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    # Відправка email для підтвердження
    try:
        token = create_access_token(
            data={"sub": user.email},
            expires_delta=timedelta(hours=24)
        )
        await send_verification_email(user.email, token)
    except Exception as e:
        logger.error(f"Failed to send verification email: {e}")
        # Продовжуємо роботу навіть якщо email не відправлено

    return db_user  

async def update_user_avatar(user_id: int, avatar_url: str, db: AsyncSession):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.avatar = avatar_url
    await db.commit()
    await db.refresh(user)
    return user

async def update_avatar(self, email: str, url: str):
    user = await self.get_user_by_email(email)
    user.avatar = url
    await self.session.commit()
    await self.session.refresh(user)
    return user

async def get_user_by_id(user_id: int, db: AsyncSession) -> Optional[User]:
    result = await db.execute(select(User).filter_by(id=user_id))
    return result.scalars().first()