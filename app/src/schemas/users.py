from pydantic import BaseModel, EmailStr, Field
class UserCreate(BaseModel):
    email: EmailStr 
    password: str   
class UserResponse(BaseModel): 
    id: int
    email: EmailStr
    confirmed: bool = False
    avatar: str | None
    class Config:
        from_attributes = True      
class Token(BaseModel):
    access_token: str
    token_type: str
class UserEmailSchema(BaseModel):
    email: EmailStr
class ResetPasswordSchema(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6)
    
class UserModel(BaseModel):
    email: EmailStr
    password: str

    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "string"
            }
        }