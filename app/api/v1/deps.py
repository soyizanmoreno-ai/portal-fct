from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.security import ALGORITHM, SECRET_KEY
from app.db.session import SessionLocal
from app.models.user import User
from app.schemas.token import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str= payload.get("sub")

        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="El email o la contraseña son incorrectos") 

        
        token_data = TokenData(email=email)

    except(jwt.PyJWTError, ValidationError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No se han podido validar las credenciales")  

    user = db.query(User).filter(User.email == token_data.email).first()

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No se han podido validar las credenciales")
    
    return user


def get_current_company_user(
    current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "empresa":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="El usuario no tiene permisos de empresa")
    return current_user