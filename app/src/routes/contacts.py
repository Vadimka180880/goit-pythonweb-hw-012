from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.src.database import get_db
from app.src.database.models import Contact, User
from app.src.repository import contacts as repository_contacts
from app.src.schemas.contacts import ContactCreate, ContactUpdate, ContactResponse, ContactModel
from app.src.services.auth import get_current_user
from app.src.database.models import User
from app.src.repository.contacts import get_contact
from datetime import date, timedelta
from typing import List   

router = APIRouter(prefix="/contacts", tags=["contacts"])

@router.post("/", response_model=ContactResponse)
async def create_contact(
    body: ContactModel,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    contact = await repository_contacts.create_contact(body, current_user.id, db)
    return contact

@router.get("/", response_model=List[ContactResponse])
async def get_contacts(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    contacts = await repository_contacts.get_contacts(current_user.id, skip, limit, db)
    return contacts

@router.get(
    "/{contact_id}",
    response_model=ContactResponse,
    summary="Get a contact by ID",
    description="Retrieves a single contact by its ID. The contact must belong to the authenticated user."
)
async def read_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    contact = await get_contact(db, contact_id, current_user)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contact with ID {contact_id} not found or does not belong to user {current_user.email}. Please check the ID or your permissions."
        )
    return contact

@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: int,
    contact: ContactUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):  
    """
    Update a contact
    """
    db_contact = await repository_contacts.update_contact(db, contact_id, contact, current_user.id)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact

@router.delete("/{contact_id}", response_model=ContactResponse)
async def delete_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a contact
    """
    db_contact = await repository_contacts.delete_contact(db, contact_id, current_user.id)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact

@router.get("/search/", response_model=List[ContactResponse])
async def search_contacts(
    query: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search contacts by name or email
    """
    contacts = await repository_contacts.search_contacts(db, query, current_user.id)
    return contacts

@router.get("/upcoming_birthdays/", response_model=List[ContactResponse])
async def get_upcoming_birthdays(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get contacts with birthdays in the next 7 days
    """
    contacts = await repository_contacts.upcoming_birthdays(db, current_user.id)
    return contacts

@router.get("/", response_model=List[ContactResponse])
async def get_contacts(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    contacts = await repository_contacts.get_contacts(current_user.id, skip, limit, db)
    return contacts

@router.post("/", response_model=ContactResponse)
async def create_contact(
    body: ContactModel,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    contact = await repository_contacts.create_contact(body, current_user.id, db)
    return contact

@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: int,
    body: ContactModel,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    contact = await repository_contacts.update_contact(contact_id, body, current_user.id, db)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact

@router.delete("/{contact_id}", response_model=dict)
async def delete_contact(
    contact_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    success = await repository_contacts.delete_contact(contact_id, current_user.id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"message": "Contact deleted successfully"}