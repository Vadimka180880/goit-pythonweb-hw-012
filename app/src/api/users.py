from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi_limiter.depends import RateLimiter

from app.src.database.database import get_db
from app.src.database.models import User
from app.src.schemas.users import UserResponse, UserCreate, Token
from app.src.config.config import settings
from app.src.services.cloudinary_service import upload_avatar
from app.src.services.email import send_verification_email

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_user_by_email(email: str, db: AsyncSession) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()  

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials", 
        headers={"WWW-Authenticate": "Bearer"}, 
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])  
        email: str = payload.get("sub") 
        if email is None:
            raise credentials_exception
    except JWTError:        
        raise credentials_exception 

    user = await get_user_by_email(email, db)
    if user is None:
        raise credentials_exception
    return user

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire}) 
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)  
    return encoded_jwt

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(new_user: UserCreate, db: AsyncSession = Depends(get_db)):
    existing_user = await get_user_by_email(new_user.email, db)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    hashed_password = get_password_hash(new_user.password)
    db_user = User(email=new_user.email, password=hashed_password)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    # Send verification email
    token = create_access_token(data={"sub": db_user.email})
    await send_verification_email(db_user.email, token)

    return db_user

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    user = await get_user_by_email(form_data.username, db)
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes) 
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_user),
    dependencies=[Depends(RateLimiter(times=5, seconds=60))]
):
    return current_user

@router.get("/verify-email")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm]) 
        email: str = payload.get("sub")
        if not email:
            raise HTTPException(status_code=400, detail="Invalid token")
        
        user = await get_user_by_email(email, db)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user.confirmed:
            return {"message": "Email already verified"}
        
        user.confirmed = True
        await db.commit()
        return {"message": "Email verified successfully"}
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid token")

@router.patch("/avatar", response_model=UserResponse)
async def update_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    avatar_url = await upload_avatar(file)
    current_user.avatar = avatar_url
    await db.commit()
    await db.refresh(current_user)
    return current_user