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

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    """
    Gets the currently authenticated user based on the JWT token.

    Args:
        token (str): JWT token from the Authorization header.
        db (AsyncSession): Async database session.

    Returns:
        User: User object.

    Raises:
        HTTPException: If the token is invalid or user not found.
    """
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

    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalars().first()
    
    if user is None:
        raise credentials_exception
    return user

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