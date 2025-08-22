from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SKUReferenceCreate(BaseModel):
    sku_name: str
    brand: str
    image_url: str
    created_by: str
    trained: bool = False

class SKUReferenceUpdate(BaseModel):
    sku_name: Optional[str] = None
    brand: Optional[str] = None
    image_url: Optional[str] = None
    trained: Optional[bool] = None

class SKUReferenceResponse(BaseModel):
    id: str
    sku_name: str
    brand: str
    image_url: str
    trained: bool
    created_by: str
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }