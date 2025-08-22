from beanie import Document, PydanticObjectId
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from enum import Enum
from typing import Optional

class UserRole(str, Enum):
    field_user = "field_user"
    admin = "admin"

class User(Document):
    id: Optional[PydanticObjectId] = Field(alias="_id", default=None)
    name: str
    email: EmailStr = Field(..., unique=True)
    password_hash: str
    role: UserRole = UserRole.field_user
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        collection = "users"
        
    def __repr__(self) -> str:
        return f"<User {self.email}>"