"""
Contacts API endpoints for creating and reading user contacts.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select  
from app.src.database.database import get_db
from app.src.database.models import Contact, User
from app.src.schemas.contacts import ContactCreate, ContactUpdate, ContactResponse
from app.src.services.auth import get_current_user  

router = APIRouter(prefix="/contacts", tags=["contacts"])

@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    contact: ContactCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new contact for the current user.
    """
    db_contact = Contact(**contact.dict(), user_id=current_user.id)
    db.add(db_contact)
    await db.commit()
    await db.refresh(db_contact)
    return db_contact

@router.get("/", response_model=list[ContactResponse])
async def read_contacts(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a list of contacts for the current user with pagination.
    """
    result = await db.execute(
        select(Contact)
        .where(Contact.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()