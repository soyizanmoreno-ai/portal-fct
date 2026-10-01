from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_student_user, get_db, get_current_company_user
from app.models.application import Application
from app.models.fct_log import FCTLog
from app.models.offer import Offer
from app.models.user import User
from app.schemas.fct_log import FCTLogCreate, FCTLogResponse
from app.services.notification_service import create_notification

router = APIRouter()

@router.post("/", response_model=FCTLogResponse, status_code=status.HTTP_201_CREATED)
def create_log(log_in: FCTLogCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_student_user)):
    query = select(Application).where(Application.id == log_in.application_id)
    application = db.scalar(query)

    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Postulación no encontrada")

    if application.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para imputar horas en esta postulación")
    if application.status != "aceptado":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Solo puedes registrar horas en una práctica aceptada")

    new_log = FCTLog(application_id=log_in.application_id, date = log_in.date, hours=log_in.hours, tasks=log_in.tasks)
    db.add(new_log)
    db.commit()
    db.refresh(new_log)

    offer = db.get(Offer, application.offer_id)
    if offer:
        create_notification(
            db=db,
            user_id=offer.company_id,
            title="Nuevo registro FCT pendiente",
            message=f"Un alumno ha registrado {new_log.hours} horas el día {new_log.date}.",
        )
    if current_user.tutor_id:
        create_notification(
            db=db,
            user_id=current_user.tutor_id,
            title="Nuevo registro FCT pendiente",
            message=f"Un alumno de tu tutoría ha registrado {new_log.hours} horas el día {new_log.date}.",
        )

    return new_log

@router.get("/me", response_model=list[FCTLogResponse])
def consult_log(current_user: User = Depends(get_current_student_user), db: Session = Depends(get_db)):
    query = select(FCTLog).join(Application, FCTLog.application_id == Application.id).where(Application.user_id == current_user.id)
    response = db.scalars(query).all()

    return response


@router.get("/company/pending", response_model=list[FCTLogResponse])
def get_company_pending_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_company_user),
):
    query = (
        select(FCTLog)
        .join(Application, FCTLog.application_id == Application.id)
        .join(Offer, Application.offer_id == Offer.id)
        .where(Offer.company_id == current_user.id, FCTLog.is_approved.is_(False))
        .order_by(FCTLog.date.desc(), FCTLog.id.desc())
    )
    return db.scalars(query).all()

@router.put("/{log_id}/approve", response_model=FCTLogResponse)
def approve_log(log_id: int, current_user: User = Depends(get_current_company_user), db: Session = Depends(get_db)):
    log = db.get(FCTLog, log_id)
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro de FCT no encontrado")

    application = db.get(Application, log.application_id)
    offer = db.get(Offer, application.offer_id) if application else None

    if not offer or offer.company_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="No tienes permiso para aprobar este registro de prácticas")

    if application.status != "aceptado":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="La candidatura no está aceptada")
    if log.is_approved:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="La empresa ya aprobó este registro")

    log.is_approved = True
    db.commit()
    db.refresh(log)

    create_notification(
        db=db,
        user_id=application.user_id,  # Usuario de la postulación
        title="Registro FCT revisado por la empresa",
        message=f"La empresa ha revisado tus {log.hours} horas del día {log.date}.",
    )

    return log