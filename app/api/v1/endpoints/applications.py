from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select, and_
from sqlalchemy.orm import Session, selectinload
from pathlib import Path, PurePosixPath
from typing import List

from app.api.v1.deps import get_current_student_user, get_db, get_current_company_user, get_current_user
from app.models.application import Application
from app.models.offer import Offer
from app.models.user import User
from app.schemas.application import ApplicationCreate, ApplicationResponse, ApplicationStatusUpdate
from app.services.notification_service import create_notification

router = APIRouter()
CV_UPLOAD_DIR = Path("uploads/cvs").resolve()


def company_application_response(application: Application) -> ApplicationResponse:
    response = ApplicationResponse.model_validate(application)
    candidate = response.student
    if candidate is None:
        return response

    if not application.contact_shared:
        candidate.email = None
    if not candidate.profile_confirmed:
        for field in (
            "full_name", "github_url", "linkedin_url", "portfolio_url",
            "technologies", "location_city", "location_province", "education",
            "experience_projects", "availability", "languages", "soft_skills",
        ):
            value = [] if field in {
                "technologies", "education", "experience_projects", "languages", "soft_skills"
            } else None
            setattr(candidate, field, value)
    return response


@router.get("/{application_id}/cv")
def download_application_cv(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    application = db.get(Application, application_id)
    if not application or application.status == "retirada":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidatura no encontrada")

    student = db.get(User, application.user_id)
    if not student or not student.cv_url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV no encontrado")

    if current_user.role == "alumno":
        if student.id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidatura no encontrada")
    elif current_user.role == "empresa":
        offer = db.get(Offer, application.offer_id)
        if not offer or offer.company_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puedes acceder a este CV")
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para acceder a este CV")

    filename = PurePosixPath(student.cv_url).name
    if not filename.startswith(f"user_{student.id}_") or not filename.endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV no encontrado")

    file_path = (CV_UPLOAD_DIR / filename).resolve()
    if file_path.parent != CV_UPLOAD_DIR or not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV no encontrado")

    return FileResponse(file_path, media_type="application/pdf", filename="curriculum.pdf")

@router.get("/me", response_model=List[ApplicationResponse], status_code=status.HTTP_200_OK)
def consulting_application(current_user: User = Depends(get_current_student_user), db: Session = Depends(get_db)):
    query = select(Application).where(Application.user_id == current_user.id).options(selectinload(Application.offer))
    response = db.scalars(query).all()  
    return response

@router.get("/offer/{offer_id}", response_model=List[ApplicationResponse], status_code=status.HTTP_200_OK)
def get_offer_applications(offer_id: int, current_user: User = Depends(get_current_company_user), db: Session = Depends(get_db)):
    
    existing_offer = db.get(Offer, offer_id)
    if not existing_offer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La oferta no se ha encontrado")
    
    if existing_offer.company_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para consultar los postulantes de esta oferta")

    query = select(Application).where(Application.offer_id == offer_id).options(
        selectinload(Application.student), selectinload(Application.offer)
    )
    response = db.scalars(query).all()

    return [company_application_response(application) for application in response]

@router.post("/", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_application(app_in: ApplicationCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_student_user)):
    # 1. Comprobar si la oferta existe
    existing_offer = db.get(Offer, app_in.offer_id)
    if existing_offer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Oferta no encontrada")
    if not existing_offer.is_active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="La oferta ya no acepta candidaturas")

    
    query = select(Application).where(and_(Application.user_id == current_user.id,Application.offer_id == app_in.offer_id))
    application_exists = db.scalar(query)
    
    if application_exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ya te has postulado a esta oferta")

   
    new_application = Application(user_id=current_user.id, offer_id=app_in.offer_id)

    db.add(new_application)
    db.commit()
    db.refresh(new_application)
    create_notification(
        db=db,
        user_id=existing_offer.company_id,
        title="Nueva candidatura",
        message=f"Un alumno se ha postulado a la oferta '{existing_offer.title}'.",
    )

    return new_application


@router.patch("/{application_id}/withdraw", response_model=ApplicationResponse)
def withdraw_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student_user),
):
    application = db.get(Application, application_id)
    if not application or application.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidatura no encontrada")

    if application.status not in {"pendiente", "en_revision", "entrevista"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Solo se pueden retirar candidaturas pendientes de decisión.",
        )

    offer = db.get(Offer, application.offer_id)
    application.status = "retirada"
    db.commit()
    db.refresh(application)

    if offer:
        create_notification(
            db=db,
            user_id=offer.company_id,
            title="Candidatura retirada",
            message=f"Un alumno ha retirado su candidatura a '{offer.title}'.",
        )

    return application


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
    if status_update.status == "entrevista":
        application.contact_shared = True

    db.add(application)
    db.commit()
    db.refresh(application)

    create_notification(
        db=db,
        user_id=application.user_id,
        title="Actualización de Candidatura",
        message=f"El estado de tu postulación ha cambiado a: '{status_update.status}'."
    )

    return company_application_response(application)
