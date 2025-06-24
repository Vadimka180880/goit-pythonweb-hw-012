"""
Repository functions for managing users in the database: CRUD, avatar, and email verification.
"""

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

# USER RETRIEVAL
async def get_user_by_email(email: str, db: AsyncSession) -> User | None:
    """
    Retrieve a user by email address.
    """
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()

# USER CREATION
async def create_user(user: UserCreate, db: AsyncSession) -> User:
    def debug(msg):
        with open("debug_user.txt", "a") as f:
            f.write(msg + "\n")
    debug(f"CREATE_USER CALLED: {user}")
    existing_user = await get_user_by_email(user.email, db)
    debug(f"EXISTING_USER: {existing_user}")
    if existing_user:
        debug("USER ALREADY EXISTS")
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    debug("BEFORE HASH")
    hashed_password = pwd_context.hash(user.password)
    debug(f"HASHED_PASSWORD: {hashed_password}")
    db_user = User(email=user.email, password=hashed_password, role=getattr(user, 'role', 'user'))
    debug(f"DB_USER: {db_user}")
    db.add(db_user)
    debug("BEFORE COMMIT")
    await db.commit()
    debug("AFTER COMMIT")
    await db.refresh(db_user)
    debug(f"AFTER REFRESH: {db_user}")
    try:
        token = create_access_token(
            data={"sub": user.email},
            expires_delta=timedelta(hours=24)
        )
        await send_verification_email(user.email, token)
    except Exception as e:
        debug(f"EMAIL EXCEPTION: {e}")
        logger.error(f"Failed to send verification email: {e}")
        # Continue even if email sending fails
    debug("RETURNING DB_USER")
    return db_user  

# AVATAR MANAGEMENT
async def update_user_avatar(user_id: int, avatar_url: str, db: AsyncSession):
    """
    Update the avatar URL for a user by user ID.
    """
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.avatar = avatar_url
    await db.commit()
    await db.refresh(user)
    return user

async def update_avatar(self, email: str, url: str):
    """
    Update the avatar URL for a user by email (method stub).
    """
    pass

# USER RETRIEVAL BY ID
async def get_user_by_id(user_id: int, db: AsyncSession) -> Optional[User]:
    """
    Retrieve a user by their unique ID.
    """
    result = await db.execute(select(User).filter_by(id=user_id))
    return result.scalars().first()