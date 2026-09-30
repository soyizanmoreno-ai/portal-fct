from pydantic import BaseModel


class StudentStatsResponse(BaseModel):
    total_applications: int = 0
    total_hours_logged: float = 0.0
    approved_hours: float = 0.0
    pending_hours: float = 0.0


class CompanyStatsResponse(BaseModel):
    total_offers: int = 0
    total_applications_received: int = 0
    pending_fct_approvals: int = 0