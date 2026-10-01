from datetime import datetime
from pydantic import BaseModel, ConfigDict

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
    student: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)