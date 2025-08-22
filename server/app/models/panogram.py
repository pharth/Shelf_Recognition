from beanie import Document, PydanticObjectId
from pydantic import Field
from typing import Optional
from datetime import datetime

class Planogram(Document):
    id: Optional[PydanticObjectId] = Field(default=None, alias="_id")
    store_id: str  
    planogram_name: str  
    layout_image: str  
    created_by: str  
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "planograms"  
        
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }