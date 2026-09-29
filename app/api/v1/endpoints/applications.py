from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_student_user, get_db
from app.models.application import Application
from app.models.offer import Offer
from app.models.user import User
from app.schemas.application import ApplicationCreate, ApplicationResponse

router = APIRouter()

@router.post("/", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_application(app_in: ApplicationCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_student_user)):
    # 1. Comprobar si la oferta existe
    existing_offer = db.get(Offer, app_in.offer_id)
    if existing_offer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Oferta no encontrada")

    # 2. Comprobar si el alumno ya se postuló
    query = select(Application).where(and_(Application.user_id == current_user.id,Application.offer_id == app_in.offer_id))
    application_exists = db.scalar(query)
    
    if application_exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ya te has postulado a esta oferta")

    # 3. Guardar la nueva postulación
    new_application = Application(user_id=current_user.id, offer_id=app_in.offer_id)

    db.add(new_application)
    db.commit()
    db.refresh(new_application)

    return new_application