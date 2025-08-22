from beanie import Document, PydanticObjectId
from pydantic import Field
from typing import Optional
from datetime import datetime

class SKUReference(Document):
    id: Optional[PydanticObjectId] = Field(default=None, alias="_id")
    sku_name: str  
    brand: str  
    image_url: str  
    trained: bool = Field(default=False)  
    created_by: str  
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "sku_references"  
        
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }