from fastapi import FastAPI, Depends
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from fastapi.middleware.cors import CORSMiddleware
from app.src.routes import auth_router, users_router, contacts_router
from app.src.database.models import User
from app.src.services.auth import get_current_user
import redis.asyncio as redis
from app.src.config.config import settings

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.allowed_origins.split(",") if settings.allowed_origins else ["*"]],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ініціалізація Redis
redis_client = redis.from_url(settings.redis_url)

# Ініціалізація FastAPILimiter
app.state.limiter = FastAPILimiter  
app.state.redis = redis_client  

@app.on_event("startup")
async def startup():
    """
    Initializes the application on startup.

    Sets up FastAPILimiter with Redis for rate limiting.

    Raises:
        Exception: If Redis or FastAPILimiter initialization fails.
    """
    await FastAPILimiter.init(app.state.redis)  

@app.on_event("shutdown")
async def shutdown():
    """
    Closes Redis connection on application shutdown.

    Cleans up FastAPILimiter resources.

    Raises:
        Exception: If connection closure fails.
    """
    await FastAPILimiter.close() 

# Routes
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(contacts_router, prefix="/contacts", tags=["contacts"])

@app.get("/users/me", dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Returns the profile of the currently authenticated user.

    Args:
        current_user (User): User object retrieved from dependency.

    Returns:
        User: Data of the current user.

    Raises:
        HTTPException: If access is denied or user is not authenticated.
    """
    return current_user