from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PlanogramCreate(BaseModel):
    store_id: str
    planogram_name: str
    layout_image: str
    created_by: str

class PlanogramUpdate(BaseModel):
    planogram_name: Optional[str] = None
    layout_image: Optional[str] = None

class PlanogramResponse(BaseModel):
    id: str
    store_id: str
    planogram_name: str
    layout_image: str
    created_by: str
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }