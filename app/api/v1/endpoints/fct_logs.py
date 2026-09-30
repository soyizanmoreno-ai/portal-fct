from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_student_user, get_db, get_current_company_user
from app.models.application import Application
from app.models.fct_log import FCTLog
from app.models.user import User
from app.schemas.fct_log import FCTLogCreate, FCTLogResponse

router = APIRouter()

@router.post("/", response_model=FCTLogResponse, status_code=status.HTTP_201_CREATED)
def create_log(log_in: FCTLogCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_student_user)):
    query = select(Application).where(Application.id == log_in.application_id)
    application = db.scalar(query)

    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Postulación no encontrada")

    if application.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para imputar horas en esta postulación")

    new_log = FCTLog(application_id=log_in.application_id, date = log_in.date, hours=log_in.hours, tasks=log_in.tasks)
    db.add(new_log)
    db.commit()
    db.refresh(new_log)

    return new_log

@router.get("/me", response_model=list[FCTLogResponse])
def consult_log(current_user: User = Depends(get_current_student_user), db: Session = Depends(get_db)):
    query = select(FCTLog).join(Application, FCTLog.application_id == Application.id).where(Application.user_id == current_user.id)
    response = db.scalars(query).all()

    return response

@router.put("/{log_id}/approve", response_model=FCTLogResponse)
def approve_log(log_id: int, current_user: User = Depends(get_current_company_user)):
    log = db.get(FCTLog, log_id)
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro de FCT no encontrado")

    application = db.get(Application, log.application_id)
    offer = db.get(Offer, application.offer_id) if application else None

    if not offer or offer.company_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="No tienes permiso para aprobar este registro de prácticas")

    log.is_approved = True
    db.commit()
    db.refresh(log)

    return log