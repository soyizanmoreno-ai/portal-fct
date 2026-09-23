from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.v1.deps import get_db
from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.schemas.token import Token

router = APIRouter()

@router.post("/login", response_model=Token)
def login_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    # 1. Busca el usuario en la BD (Nota: OAuth2PasswordRequestForm guarda el email en 'form_data.username')
    user = db.query(User).filter(User.email == form_data.username).first()

    # 2. Comprueba si el usuario NO existe O si la contraseña es incorrecta con verify_password()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")
  
    access_token = create_access_token(subject=user.email)

    return {"access_token": access_token, "token_type": "bearer"}
