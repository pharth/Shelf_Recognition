from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class ShelfAnalysisCreate(BaseModel):
    image_id: str
    osa_percent: float
    sos_percent: float
    planogram_match: bool
    raw_output_json: Dict[str, Any]

class ShelfAnalysisUpdate(BaseModel):
    osa_percent: Optional[float] = None
    sos_percent: Optional[float] = None
    planogram_match: Optional[bool] = None
    raw_output_json: Optional[Dict[str, Any]] = None

class ShelfAnalysisResponse(BaseModel):
    id: str
    image_id: str
    osa_percent: float
    sos_percent: float
    planogram_match: bool
    analysis_time: datetime
    raw_output_json: Dict[str, Any]
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }