from beanie import Document, PydanticObjectId
from pydantic import Field
from typing import Optional, Dict, Any
from datetime import datetime

class ShelfAnalysis(Document):
    id: Optional[PydanticObjectId] = Field(default=None, alias="_id")
    image_id: str  
    osa_percent: float  
    sos_percent: float  
    planogram_match: bool  
    analysis_time: datetime = Field(default_factory=datetime.utcnow)
    raw_output_json: Dict[str, Any]  
    
    class Settings:
        name = "shelf_analysis"  
        
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }