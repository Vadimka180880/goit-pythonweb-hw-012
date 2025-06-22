from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.src.database.base import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    confirmed = Column(Boolean, default=False)
    avatar = Column(String, nullable=True)
    contacts = relationship("Contact", back_populates="owner")  

class Contact(Base):  
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    phone = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))  
    owner = relationship("User", back_populates="contacts")  