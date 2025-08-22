from beanie import Document
from pydantic import Field
from typing import Optional
from datetime import datetime
from decimal import Decimal

class Image(Document):
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str  
    store_id: str  
    image_url: str  
    latitude: Decimal  
    longitude: Decimal  
    upload_time: datetime = Field(default_factory=datetime.utcnow)
    is_deleted: bool = Field(default=False)  
    
    class Settings:
        name = "images"  
        
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }