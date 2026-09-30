from pydantic import BaseModel, ConfigDict
from datetime import date 

class FCTLogBase(BaseModel):
    application_id: int
    date: date
    hours: float
    tasks: str 

class FCTLogCreate(FCTLogBase):
    pass
    
class FCTLogResponse(BaseModel):
    id: int
    is_approved: bool 

    model_config = ConfigDict(from_attributes=True)


