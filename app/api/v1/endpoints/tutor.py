from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload

from app.api.v1 import deps
from app.models.user import User
from app.models.company import CompanyProfile
from app.models.application import Application
from app.models.fct_log import FCTLog
from app.schemas.tutor import StudentFCTSummary
from app.schemas.fct_log import FCTLogResponse
from app.schemas.user import UserResponse
from app.services.notification_service import create_notification

router = APIRouter()

@router.post("/assign-student/{student_id}", response_model=UserResponse)
def assign_student_to_tutor(
    student_id: int,
    db: Session = Depends(deps.get_db),
    current_tutor: User = Depends(deps.get_current_tutor_user),
):
    """Vincula un alumno a la tutoría del usuario tutor autenticado."""
    student = db.get(User, student_id)
    if not student or student.role != "alumno":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El alumno especificado no existe o no tiene rol de alumno."
        )
    
    student.tutor_id = current_tutor.id
    db.add(student)
    db.commit()
    db.refresh(student)
    return student

@router.get("/my-students", response_model=List[StudentFCTSummary])
def get_my_students_fct_summary(
    db: Session = Depends(deps.get_db),
    current_tutor: User = Depends(deps.get_current_tutor_user),
):
    """Obtiene la lista de alumnos tutorizados y su resumen de horas en tiempo real."""
    students = db.scalars(
        select(User).where(User.tutor_id == current_tutor.id)
    ).all()

    summaries = []
    for student in students:
        
        app = db.scalar(
            select(Application).where(
                Application.user_id == student.id,
                Application.status == "aceptado"
            ).options(selectinload(Application.offer)).limit(1)
        )

        company_profile = (
            db.scalar(select(CompanyProfile).where(CompanyProfile.user_id == app.offer.company_id))
            if app
            else None
        )
        company_name = company_profile.company_name if company_profile else None
        offer_title = app.offer.title if app else None
        student_status = "en_practicas" if app else "sin_practicas"

        
        total_hours = db.scalar(
            select(func.coalesce(func.sum(FCTLog.hours), 0.0))
            .join(Application)
            .where(Application.user_id == student.id)
        ) or 0.0

        
        approved_hours = db.scalar(
            select(func.coalesce(func.sum(FCTLog.hours), 0.0))
            .join(Application)
            .where(
                Application.user_id == student.id,
                FCTLog.is_approved.is_(True),
                FCTLog.is_tutor_approved.is_(True),
            )
        ) or 0.0

        summaries.append(
            StudentFCTSummary(
                student=student,
                company_name=company_name,
                offer_title=offer_title,
                total_hours_registered=float(total_hours),
                total_hours_approved=float(approved_hours),
                status=student_status,
            )
        )

    return summaries

@router.get("/student/{student_id}/fct-logs", response_model=List[FCTLogResponse])
def get_student_fct_logs(
    student_id: int,
    db: Session = Depends(deps.get_db),
    current_tutor: User = Depends(deps.get_current_tutor_user),
):
    """Permite al tutor revisar el cuaderno de prácticas detallado de uno de sus alumnos."""
    student = db.get(User, student_id)
    if not student or student.tutor_id != current_tutor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver el cuaderno de este alumno o no pertenece a tu tutoría."
        )

    logs = db.scalars(
        select(FCTLog)
        .join(Application)
        .where(Application.user_id == student_id)
    ).all()

    return logs


@router.put("/student/{student_id}/fct-logs/{log_id}/approve", response_model=FCTLogResponse)
def approve_student_fct_log(
    student_id: int,
    log_id: int,
    db: Session = Depends(deps.get_db),
    current_tutor: User = Depends(deps.get_current_tutor_user),
):
    student = db.get(User, student_id)
    if not student or student.tutor_id != current_tutor.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alumno no encontrado en tu tutoría")

    log = db.get(FCTLog, log_id)
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro de FCT no encontrado")

    application = db.get(Application, log.application_id)
    if not application or application.user_id != student.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro de FCT no encontrado")
    if application.status != "aceptado":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="La candidatura no está aceptada")
    if log.is_tutor_approved:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El tutor ya aprobó este registro")

    log.is_tutor_approved = True
    db.commit()
    db.refresh(log)
    create_notification(
        db=db,
        user_id=student.id,
        title="Registro FCT revisado por el tutor",
        message=f"Tu tutor ha revisado las {log.hours} horas del día {log.date}.",
    )
    return log