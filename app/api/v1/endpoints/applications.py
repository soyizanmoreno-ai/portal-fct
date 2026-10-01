from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.orm import Session, selectinload
from typing import List

from app.api.v1.deps import get_current_student_user, get_db, get_current_company_user
from app.models.application import Application
from app.models.offer import Offer
from app.models.user import User
from app.schemas.application import ApplicationCreate, ApplicationResponse
from app.services.notification_service import create_notification

router = APIRouter()

@router.get("/me", response_model=List[ApplicationResponse], status_code=status.HTTP_200_OK)
def consulting_application(current_user: User = Depends(get_current_student_user), db: Session = Depends(get_db)):
    query = select(Application).where(Application.user_id == current_user.id)
    response = db.scalars(query).all()  
    return response

@router.get("/offer/{offer_id}", response_model=List[ApplicationResponse], status_code=status.HTTP_200_OK)
def get_offer_applications(offer_id: int, current_user: User = Depends(get_current_company_user), db: Session = Depends(get_db)):
    
    existing_offer = db.get(Offer, offer_id)
    if not existing_offer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La oferta no se ha encontrado")
    
    if existing_offer.company_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para consultar los postulantes de esta oferta")

    query = select(Application).where(Application.offer_id == offer_id).options(selectinload(Application.student))
    response = db.scalars(query).all()

    return response 

@router.post("/", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_application(app_in: ApplicationCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_student_user)):
    # 1. Comprobar si la oferta existe
    existing_offer = db.get(Offer, app_in.offer_id)
    if existing_offer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Oferta no encontrada")

    
    query = select(Application).where(and_(Application.user_id == current_user.id,Application.offer_id == app_in.offer_id))
    application_exists = db.scalar(query)
    
    if application_exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ya te has postulado a esta oferta")

   
    new_application = Application(user_id=current_user.id, offer_id=app_in.offer_id)

    db.add(new_application)
    db.commit()
    db.refresh(new_application)

    return new_application


@router.put("/{application_id}/status", response_model=ApplicationResponse, status_code=status.HTTP_200_OK)
def update_application_status(
    application_id: int,
    status_update: ApplicationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_company_user),
):
    
    application = db.get(Application, application_id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="La candidatura no se ha encontrado"
        )

    
    offer = db.get(Offer, application.offer_id)
    if not offer or offer.company_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="No tienes permiso para modificar esta candidatura"
        )

    
    valid_statuses = ["pendiente", "en_revision", "entrevista", "aceptado", "rechazado"]
    if status_update.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Estado no válido. Debe ser uno de los siguientes: {', '.join(valid_statuses)}"
        )

   
    application.status = status_update.status
    if status_update.feedback is not None:
        application.feedback = status_update.feedback

    db.add(application)
    db.commit()
    db.refresh(application)

    return application

    create_notification(
        db=db,
        user_id=application.user_id,
        title="Actualización de Candidatura",
        message=f"El estado de tu postulación ha cambiado a: '{status_update.status}'."
    )

