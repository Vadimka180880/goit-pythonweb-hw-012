from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.src.database.models import Contact, User
from app.src.schemas.contacts import ContactModel
from typing import Optional, List

async def get_contacts(user_id: int, skip: int, limit: int, db: AsyncSession):
    return db.query(Contact).filter(Contact.user_id == user_id).offset(skip).limit(limit).all()

async def create_contact(body: ContactModel, user_id: int, db: AsyncSession):
    contact = Contact(**body.dict(), user_id=user_id)
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact

async def get_contact(contact_id: int, user_id: int, db: AsyncSession) -> Optional[Contact]:
    result = await db.execute(select(Contact).filter_by(id=contact_id, user_id=user_id))
    return result.scalars().first()

async def update_contact(contact_id: int, body: ContactModel, user_id: int, db: AsyncSession) -> Optional[Contact]:
    contact = await get_contact(contact_id, user_id, db)
    if contact:
        contact.first_name = body.first_name
        contact.last_name = body.last_name
        contact.email = body.email
        contact.phone = body.phone
        contact.birthday = body.birthday
        await db.commit()
        await db.refresh(contact)
    return contact

async def delete_contact(contact_id: int, user_id: int, db: AsyncSession) -> bool:
    contact = await get_contact(contact_id, user_id, db)
    if contact:
        await db.delete(contact)
        await db.commit()
        return True
    return False