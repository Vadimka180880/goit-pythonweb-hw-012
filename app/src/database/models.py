"""
SQLAlchemy ORM models for User and Contact tables.
Defines User (with role) and Contact models and their relationships.
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.src.database.base import Base

class User(Base):
    """
    SQLAlchemy model for the users table.
    """
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    confirmed = Column(Boolean, default=False)
    avatar = Column(String, nullable=True)
    role = Column(String, default="user")  # user/admin
    contacts = relationship("Contact", back_populates="owner")  

class Contact(Base):  
    """
    SQLAlchemy model for the contacts table.
    """
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    phone = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))  
    owner = relationship("User", back_populates="contacts")