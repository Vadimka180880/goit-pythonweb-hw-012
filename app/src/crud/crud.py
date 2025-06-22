from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from app.src.database import models 
from datetime import date, timedelta

async def search_contacts(db: AsyncSession, query: str):     
    result = await db.execute(  
        select(models.Contact).where(
            or_(     
                models.Contact.first_name.ilike(f"%{query}%"),
                models.Contact.last_name.ilike(f"%{query}%"),
                models.Contact.email.ilike(f"%{query}%")     
            )
        )
    )  
    return result.scalars().all()

async def upcoming_birthdays(db: AsyncSession):
    today = date.today()      
    upcoming_date = today + timedelta(days=7)   
    result = await db.execute(       
        select(models.Contact).where(   
            func.to_char(models.Contact.birthday, 'MM-DD').between(
                today.strftime('%m-%d'),     
                upcoming_date.strftime('%m-%d')
            ) 
        ) 
    ) 
    return result.scalars().all()     
