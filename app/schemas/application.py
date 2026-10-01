from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.offer import OfferResponse
from app.schemas.user import StudentCandidateResponse

class ApplicationCreate(BaseModel):
    offer_id: int 

class ApplicationStatusUpdate(BaseModel):
    status: str  
    feedback: Optional[str] = None

class ApplicationResponse(BaseModel):
    id: int
    user_id: int
    offer_id: int
    status: str
    feedback: Optional[str] = None
    created_at: datetime
    student: Optional[StudentCandidateResponse] = None
    offer: Optional[OfferResponse] = None

    model_config = ConfigDict(from_attributes=True)