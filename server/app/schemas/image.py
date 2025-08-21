from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ImageUploadResponse(BaseModel):
    image_id: str
    status: str
    message: str

class ImageAnalysisResponse(BaseModel):
    image_id: str
    osa_percent: float
    sos_percent: float
    planogram_compliance: bool
    analysis_time: datetime
    status: str

class ImageHistoryResponse(BaseModel):
    images: List[dict]
    total: int