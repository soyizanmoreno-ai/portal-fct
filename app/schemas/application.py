from datetime import datetime
from pydantic import BaseModel, ConfigDict

class ApplicationCreate(BaseModel):
    offer_id: int 

class ApplicationResponse(BaseModel):
    id: int 
    user_id: int 
    offer_id: int 
    created_at: datetime 

    model_config = ConfigDict(from_attributes=True) 
