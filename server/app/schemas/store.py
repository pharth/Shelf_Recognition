from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal

class StoreCreate(BaseModel):
    name: str
    store_code: str
    address: str
    city: str
    state: str
    latitude: Decimal
    longitude: Decimal

class StoreUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None

class StoreResponse(BaseModel):
    id: str
    name: str
    store_code: str
    address: str
    city: str
    state: str
    latitude: Decimal
    longitude: Decimal
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }