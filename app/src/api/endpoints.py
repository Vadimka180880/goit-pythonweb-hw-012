from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.src.database.database import get_db
from app.src.schemas import ContactCreate, ContactUpdate, ContactResponse
from app.src.repository import contacts as repository_contacts

router = APIRouter()    

@router.post("/contacts/", response_model=ContactResponse)
async def create_contact(contact: ContactCreate, db: AsyncSession = Depends(get_db)):
    return await repository_contacts.create_contact(db, contact)    

@router.get("/contacts/", response_model=List[ContactResponse]) 
async def get_contacts(db: AsyncSession = Depends(get_db)):  
    return await repository_contacts.get_contacts(db)  

@router.get("/contacts/{contact_id}", response_model=ContactResponse)
async def get_contact(contact_id: int, db: AsyncSession = Depends(get_db)):
    contact = await repository_contacts.get_contact(db, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact  

@router.put("/contacts/{contact_id}", response_model=ContactResponse)   
async def update_contact(contact_id: int, contact: ContactUpdate, db: AsyncSession = Depends(get_db)):
    updated = await repository_contacts.update_contact(db, contact_id, contact) 
    if not updated: 
        raise HTTPException(status_code=404, detail="Contact not found")
    return updated 

@router.delete("/contacts/{contact_id}")
async def delete_contact(contact_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await repository_contacts.delete_contact(db, contact_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"detail": "Contact deleted"}    

@router.get("/contacts/search/", response_model=List[ContactResponse]) 
async def search_contacts(query: str = Query(..., min_length=1), db: AsyncSession = Depends(get_db)):
    return await repository_contacts.search_contacts(db, query) 

@router.get("/contacts/upcoming_birthdays/", response_model=List[ContactResponse])
async def upcoming_birthdays(db: AsyncSession = Depends(get_db)):   
    return await repository_contacts.upcoming_birthdays(db)  
