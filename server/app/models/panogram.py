from beanie import Document
from pydantic import Field
from typing import Optional
from datetime import datetime

class Planogram(Document):
    id: Optional[str] = Field(default=None, alias="_id")
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