"""
Pydantic schemas for contact data validation and response models.
"""

from pydantic import BaseModel, EmailStr, ConfigDict, Field
from datetime import date
from typing import Optional

class ContactBase(BaseModel):
    """
    Base schema for contact information with validation.
    """
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    phone_number: str = Field(..., pattern=r"^\+?[1-9]\d{1,14}$")  
    birthday: date
    additional_info: Optional[str] = Field(None, max_length=300)

class ContactResponse(ContactBase):
    """
    Schema for returning contact information in responses.
    """
    id: int
    user_id: int  
    model_config = ConfigDict(from_attributes=True)  

class ContactUpdate(BaseModel):     
    """
    Schema for updating contact information with validation.
    """
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None 
    phone_number: Optional[str] = Field(None, pattern=r"^\+?[1-9]\d{1,14}$")
    birthday: Optional[date] = None
    additional_info: Optional[str] = Field(None, max_length=300)