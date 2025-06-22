"""
Authentication and authorization service functions: password hashing, JWT, user retrieval, admin check, avatar, and password reset.
"""

from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, UploadFile, status
from fastapi.security import HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.src.config.config import settings
from app.src.database.models import User  
from app.src.database.database import get_db  
import secrets
from app.src.services.email import send_verification_email
from app.src.schemas.users import UserModel

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/auth/login")
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# PASSWORD HASHING

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Checks if the entered password matches the hash.

    Args:
        plain_password (str): Plain text password.
        hashed_password (str): Hashed password from the database.

    Returns:
        bool: True if passwords match, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Generates a password hash using bcrypt.

    Args:
        password (str): Plain text password.

    Returns:
        str: Hashed password.
    """
    return pwd_context.hash(password)

# JWT TOKEN GENERATION

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Generates a JWT access token.

    Args:
        data (dict): Data to encode in the token (e.g., email).
        expires_delta (Optional[timedelta]): Token lifetime (default from settings).

    Returns:
        str: Encoded JWT token.

    Raises:
        JWTError: If encoding fails.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Generates a JWT refresh token.

    Args:
        data (dict): Data to encode in the token (e.g., email).
        expires_delta (Optional[timedelta]): Token lifetime (default 7 days).

    Returns:
        str: Encoded JWT refresh token.

    Raises:
        JWTError: If encoding fails.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=7))
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)

# USER RETRIEVAL & CACHING

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    """
    Gets the currently authenticated user based on the JWT token.
    Uses Redis cache for user data if available.
    """
    from app.src.database.redis import get_redis
    import json
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm]) 
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    redis_conn = None
    try:
        async for r in get_redis():
            redis_conn = r
            break
        cache_key = f"user:{email}"
        cached_user = await redis_conn.get(cache_key)
        if cached_user:
            user_dict = json.loads(cached_user)
            user = User(**user_dict)
            return user
    except Exception:
        pass  # Ignore cache if Redis is unavailable

    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalars().first()
    if user is None:
        raise credentials_exception
    try:
        if redis_conn and user:
            await redis_conn.set(cache_key, user.model_dump_json(), ex=300)  # 5 minutes
    except Exception:
        pass
    return user

async def get_current_user_from_refresh(token: str = Depends(oauth2_scheme)) -> User:
    """
    Gets user from refresh token.

    Args:
        token (str): JWT refresh token.

    Returns:
        User: Decoded user information.

    Raises:
        HTTPException: If the token is invalid or the user cannot be found.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token type")
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        # No DB here for simplicity, but can be added
        return email
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

def decode_token(token: str) -> Dict[str, Any]:
    """
    Decodes a JWT token to get the data.

    Args:
        token (str): JWT token.

    Returns:
        Dict[str, Any]: Decoded data from the token.

    Raises:
        HTTPException: If the token is invalid.
    """
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])  
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}"
        )

# ADMIN ROLE CHECK

async def get_current_active_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to check if current user is admin.
    Raises 403 if not admin.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user

# AVATAR MANAGEMENT

async def update_avatar(email: str, file: UploadFile, db: AsyncSession):
    """
    Updates the user's avatar.

    Args:
        email (str): User's email.
        file (UploadFile): Uploaded avatar file.
        db (AsyncSession): Async database session.

    Returns:
        dict: Message about successful update.

    Raises:
        HTTPException: If user not found.
    """
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    file_path = f"static/avatars/{user.id}.jpg"
    contents = await file.read()
    
    with open(file_path, "wb") as buffer:
        buffer.write(contents)

    user.avatar = file_path
    await db.commit()
    await db.refresh(user)
    
    return {"message": "Avatar updated successfully"}

# PASSWORD RESET

async def get_user_by_email(email: str, db: AsyncSession) -> Optional[User]:
    """
    Gets a user by email.

    Args:
        email (str): User's email.
        db (AsyncSession): Async database session.

    Returns:
        Optional[User]: User object or None if not found.
    """
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()

async def reset_user_password(token: str, new_password: str, db: AsyncSession) -> Optional[User]:
    """
    Resets the user's password based on the token.

    Args:
        token (str): JWT token for reset.
        new_password (str): New password.
        db (AsyncSession): Async database session.

    Returns:
        Optional[User]: User object or None if the token is invalid.

    Raises:
        HTTPException: If token decoding failed.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])  
        if payload.get("type") != "password_reset":
            return None
        
        email = payload.get("sub")
        if not email:
            return None        
        
        user = await get_user_by_email(email, db)
        if not user:
            return None
        
        user.hashed_password = pwd_context.hash(new_password)
        await db.commit()
        await db.refresh(user)
        return user
        
    except JWTError:
        return None
    
async def create_user(body: UserModel, db: AsyncSession = Depends(get_db)):
    """
    Creates a new user.

    Args:
        body (UserModel): New user data (email, password).
        db (AsyncSession): Async database session.

    Returns:
        User: Created user.

    Raises:
        HTTPException: If the email is already registered.
    """
    existing_user = await get_user_by_email(body.email, db)
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered")
    hashed_password = pwd_context.hash(body.password)
    verification_code = secrets.token_urlsafe(32)
    user = User(email=body.email, password=hashed_password, confirmed=False, verification_code=verification_code)
    db.add(user)
    db.commit()
    db.refresh(user)
    await send_verification_email(body.email, verification_code)
    return user

async def verify_email(verification_code: str, db: AsyncSession = Depends(get_db)):
    """
    Confirms the user's email by the verification code.

    Args:
        verification_code (str): Verification code.
        db (AsyncSession): Async database session.

    Returns:
        dict: Message about successful verification.

    Raises:
        HTTPException: If the code is invalid or email already verified.
    """
    user = db.query(User).filter(User.verification_code == verification_code).first()
    if not user or user.confirmed:
        raise HTTPException(status_code=400, detail="Invalid or already verified code")
    user.confirmed = True
    user.verification_code = None
    db.commit()
    return {"message": "Email verified successfully"}