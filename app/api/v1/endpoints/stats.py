from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.api.v1.deps import get_current_company_user, get_current_student_user, get_db
from app.models.application import Application
from app.models.fct_log import FCTLog
from app.models.offer import Offer
from app.models.user import User
from app.schemas.stats import CompanyStatsResponse, StudentStatsResponse

router = APIRouter()

@router.get("/student", response_model=StudentStatsResponse, status_code=status.HTTP_200_OK)
def get_student_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_student_user)):
    total_applications = db.scalar(select(func.count(Application.id)).where(Application.user_id == current_user.id)) or 0
    total_hours = float(db.scalar(select(func.coalesce(func.sum(FCTLog.hours), 0.0)).join(Application, FCTLog.application_id == Application.id).where(Application.user_id == current_user.id)) or 0.0)
    approved_hours = float(db.scalar(select(func.coalesce(func.sum(FCTLog.hours), 0.0)).join(Application, FCTLog.application_id == Application.id).where(Application.user_id == current_user.id, FCTLog.is_approved == True)) or 0.0)
    return StudentStatsResponse(total_applications=total_applications, total_hours_logged=total_hours, approved_hours=approved_hours, pending_hours=(total_hours - approved_hours))

@router.get("/company", response_model=CompanyStatsResponse, status_code=status.HTTP_200_OK)
def get_company_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_company_user)):
    total_offers = db.scalar(select(func.count(Offer.id)).where(Offer.company_id == current_user.id)) or 0
    total_apps = db.scalar(select(func.count(Application.id)).join(Offer, Application.offer_id == Offer.id).where(Offer.company_id == current_user.id)) or 0
    pending_fct = db.scalar(select(func.count(FCTLog.id)).join(Application, FCTLog.application_id == Application.id).join(Offer, Application.offer_id == Offer.id).where(Offer.company_id == current_user.id, FCTLog.is_approved == False)) or 0
    return CompanyStatsResponse(total_offers=total_offers, total_applications_received=total_apps, pending_fct_approvals=pending_fct)