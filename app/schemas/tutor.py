# app/schemas/tutor.py
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.schemas.user import UserResponse

class StudentFCTSummary(BaseModel):
    student: UserResponse
    company_name: Optional[str] = None
    offer_title: Optional[str] = None
    total_hours_registered: float
    total_hours_approved: float
    status: str

    model_config = ConfigDict(from_attributes=True)