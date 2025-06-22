"""
Routes for user-related operations.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/")
async def read_users():
    """
    Retrieve a list of users or user-related information.
    """
    return {"message": "Users endpoint"}