from pydantic import BaseModel, EmailStr
from datetime import date
from typing import Optional

class ContactBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    birthday: date
    additional_info: Optional[str] = None

class ContactCreate(ContactBase):
    pass

class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    birthday: Optional[date] = None
    additional_info: Optional[str] = None

class ContactResponse(ContactBase):
    id: int

    class Config:
        from_attributes = True

class ContactModel(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str 
    birthday: date
    user_id: int

    class Config:
            json_schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "phone": "+1234567890",
                "birthday": "1990-01-01",
                "user_id": 1
            }
        }