from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal

class ImageCreate(BaseModel):
    user_id: str
    store_id: str
    image_url: str
    latitude: Decimal
    longitude: Decimal

class ImageUpdate(BaseModel):
    image_url: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    is_deleted: Optional[bool] = None

class ImageResponse(BaseModel):
    id: str
    user_id: str
    store_id: str
    image_url: str
    latitude: Decimal
    longitude: Decimal
    upload_time: datetime
    is_deleted: bool
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }