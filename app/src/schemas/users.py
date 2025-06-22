"""
Pydantic models for user-related schemas.
"""
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    """
    Schema for creating a new user.
    """
    email: EmailStr 
    password: str   

class UserResponse(BaseModel): 
    """
    Schema for returning user information in responses.
    """
    id: int
    email: EmailStr
    confirmed: bool = False
    avatar: str | None
    class Config:
        from_attributes = True      

class Token(BaseModel):
    """
    Schema for JWT access token response.
    """
    access_token: str
    token_type: str

class UserEmailSchema(BaseModel):
    """
    Schema for user email input.
    """
    email: EmailStr

class ResetPasswordSchema(BaseModel):
    """
    Schema for password reset input.
    """
    token: str
    new_password: str = Field(..., min_length=6)
    
class UserModel(BaseModel):
    """
    Schema for user model with example.
    """
    email: EmailStr
    password: str

    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "string"
            }
        }