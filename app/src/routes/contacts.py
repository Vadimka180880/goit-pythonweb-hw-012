"""
Routes for managing user contacts: create, read, update, delete, and search contacts.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
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

router = APIRouter(tags=["contacts"])  

# CREATE CONTACT ENDPOINT
@router.post("/", response_model=ContactResponse)
async def create_contact(
    body: ContactCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new contact for the current user.
    """
    try:
        contact = await repository_contacts.create_contact(body, current_user.id, db)
    except Exception as e:
        # If double email — refound 409
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(status_code=409, detail="Contact with this email already exists.")
        raise
    first_name, last_name = (contact.name.split(' ', 1) + [""])[:2]
    data = ContactResponse(
        id=contact.id,
        first_name=first_name,
        last_name=last_name,
        email=contact.email,
        phone_number=contact.phone,
        birthday=body.birthday,
        additional_info=body.additional_info
    ).model_dump()
    if data["birthday"]:
        data["birthday"] = data["birthday"].isoformat()
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=data
    )

# GET CONTACTS ENDPOINT (paginated)
@router.get("/", response_model=List[ContactResponse])
async def get_contacts(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a paginated list of contacts for the current user.
    """
    contacts = await repository_contacts.get_contacts(current_user.id, skip, limit, db)
    return contacts

# GET SINGLE CONTACT ENDPOINT
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

# UPDATE CONTACT ENDPOINT
@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: int,
    body: ContactModel,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing contact by its ID for the current user.
    """
    contact = await repository_contacts.update_contact(contact_id, body, current_user.id, db)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact

# DELETE CONTACT ENDPOINT
@router.delete("/{contact_id}", response_model=dict)
async def delete_contact(
    contact_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a contact by its ID for the current user.
    """
    success = await repository_contacts.delete_contact(contact_id, current_user.id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"message": "Contact deleted successfully"}

# SEARCH CONTACTS ENDPOINT
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

# UPCOMING BIRTHDAYS ENDPOINT
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