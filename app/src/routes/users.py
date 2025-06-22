"""
Routes for user-related operations.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.database.models import User
from app.src.services.auth import get_current_user, get_current_active_admin
from app.src.database.base import get_db
from app.src.schemas.users import UserResponse

router = APIRouter(tags=["users"])  

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Get the profile of the currently authenticated user.
    Returns user data as a response model.
    """
    return UserResponse.from_orm(current_user)

@router.get("/all", response_model=list[UserResponse], dependencies=[Depends(get_current_active_admin)])
async def get_all_users(db: AsyncSession = Depends(get_db)):
    """
    Get a list of all users (admin only).
    Returns a list of user response models.
    """
    result = await db.execute("SELECT * FROM users")
    users = result.fetchall()
    return [UserResponse.from_orm(User(**dict(row))) for row in users]

@router.get("/")
async def read_users():
    """
    Basic endpoint for users root. Can be used for health checks or future extensions.
    """
    return {"message": "Users endpoint"}