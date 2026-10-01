import os
from pathlib import Path, PurePosixPath
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.v1 import deps
from app.api.v1.deps import get_current_user, get_db
from app.core.security import get_password_hash
from app.models.user import User
from app.models.company import CompanyProfile
from app.schemas.user import ProfileUpdate, StudentProfileResponse, UserResponse
from app.schemas.user import UserCreate
from app.schemas.company import CompanyProfileResponse, CompanyProfileUpdate
from app.services.cv_parser import CVParseError, extract_technology_suggestions

router = APIRouter()

UPLOAD_DIR = "uploads/cvs"
MAX_CV_SIZE_BYTES = 5 * 1024 * 1024


@router.get("/cv")
def download_own_cv(current_user: User = Depends(deps.get_current_student_user)):
    if not current_user.cv_url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV no encontrado")

    filename = PurePosixPath(current_user.cv_url).name
    if not filename.startswith(f"user_{current_user.id}_") or not filename.endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV no encontrado")

    upload_directory = Path(UPLOAD_DIR).resolve()
    file_path = (upload_directory / filename).resolve()
    if file_path.parent != upload_directory or not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV no encontrado")

    return FileResponse(file_path, media_type="application/pdf", filename="mi-curriculum.pdf")


@router.get("/company-profile", response_model=CompanyProfileResponse)
def read_company_profile(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_company_user),
):
    profile = db.query(CompanyProfile).filter(CompanyProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de empresa no configurado")
    return profile


@router.put("/company-profile", response_model=CompanyProfileResponse)
def update_company_profile(
    profile_data: CompanyProfileUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_company_user),
):
    profile = db.query(CompanyProfile).filter(CompanyProfile.user_id == current_user.id).first()
    if not profile:
        profile = CompanyProfile(user_id=current_user.id)
        db.add(profile)

    profile.company_name = profile_data.company_name
    profile.cif = profile_data.cif
    profile.website = str(profile_data.website) if profile_data.website else None
    try:
        db.commit()
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se pudo guardar el perfil; comprueba si ese CIF ya está registrado.",
        ) from error
    db.refresh(profile)
    return profile

@router.put("/profile", response_model=StudentProfileResponse)
def update_profile(
    profile_data: ProfileUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_student_user),
):
    """Actualiza o confirma los datos estructurados del perfil del alumno."""
    updates = profile_data.model_dump(exclude_unset=True, exclude={"confirm_profile"})
    for field, value in updates.items():
        setattr(current_user, field, value)
    if updates:
        current_user.profile_confirmed = False
    if profile_data.confirm_profile:
        current_user.profile_confirmed = True
        confirmed_names = {item["name"] for item in current_user.technologies}
        current_user.suggested_technologies = [
            item for item in current_user.suggested_technologies
            if item["name"] not in confirmed_names
        ]
    elif "confirm_profile" in profile_data.model_fields_set:
        current_user.profile_confirmed = False

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/profile", response_model=StudentProfileResponse)
def read_profile(
    current_user: User = Depends(deps.get_current_student_user),
):
    """Devuelve el perfil estructurado y las sugerencias privadas del alumno."""
    return current_user


@router.post("/upload-cv", response_model=StudentProfileResponse)
def upload_cv(
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_student_user),
):
    """Sube un PDF de CV con tamaño limitado y firma de archivo comprobada."""
    content = file.file.read(MAX_CV_SIZE_BYTES + 1)
    if len(content) > MAX_CV_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="El CV no puede superar los 5 MB.",
        )
    if b"%PDF-" not in content[:1024]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El archivo no contiene una cabecera PDF válida.")
    try:
        suggestions = extract_technology_suggestions(content)
    except CVParseError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_filename = f"user_{current_user.id}_{uuid4().hex}.pdf"
    file_path = os.path.join(UPLOAD_DIR, file_filename)

    try:
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        current_user.cv_url = f"/{UPLOAD_DIR}/{file_filename}"
        current_user.suggested_technologies = suggestions
        current_user.profile_confirmed = False
        db.add(current_user)
        db.commit()
    except (OSError, SQLAlchemyError):
        db.rollback()
        if os.path.exists(file_path):
            os.remove(file_path)
        raise
    db.refresh(current_user)
    return current_user

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_in.email).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya está registrado en esta plataforma"
        )

    db_user = User(
        email=user_in.email, 
        hashed_password=get_password_hash(user_in.password), 
        role="alumno"
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

@router.get("/me", response_model=UserResponse)
def read_user_me(current_user: User = Depends(get_current_user)):
    """
    Devuelve los datos del usuario actualmente autenticado usando su Token JWT.
    """
    return current_user


    