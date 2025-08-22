from beanie import Document, PydanticObjectId
from pydantic import Field
from typing import Optional
from datetime import datetime
from decimal import Decimal

class Store(Document):
    id: Optional[PydanticObjectId] = Field(default=None, alias="_id")
    name: str
    store_code: str = Field(unique=True)
    address: str
    city: str
    state: str
    latitude: Decimal
    longitude: Decimal
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "stores"  # MongoDB collection name
        
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }