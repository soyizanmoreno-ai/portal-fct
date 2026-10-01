from getpass import getpass
import sys

from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.security import get_password_hash
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.models.user import User


def create_initial_admin(email: str, password: str) -> None:
    email = TypeAdapter(EmailStr).validate_python(email)
    if len(password) < 12:
        raise ValueError("La contraseña debe tener al menos 12 caracteres.")

    init_db()
    db = SessionLocal()
    try:
        if db.query(User).filter(User.role == "admin").first():
            raise ValueError("Ya existe un administrador; no se creará otro.")
        if db.query(User).filter(User.email == email).first():
            raise ValueError("Ese email ya pertenece a una cuenta.")

        db.add(
            User(
                email=email,
                hashed_password=get_password_hash(password),
                role="admin",
            )
        )
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise ValueError("No se pudo crear el administrador; comprueba si ya existe.") from error
    finally:
        db.close()


def main() -> None:
    email = input("Email del administrador: ").strip()
    password = getpass("Contraseña (mínimo 12 caracteres): ")
    confirmation = getpass("Repite la contraseña: ")
    if password != confirmation:
        raise SystemExit("Las contraseñas no coinciden.")

    try:
        create_initial_admin(email, password)
    except (ValueError, ValidationError, SQLAlchemyError) as error:
        print(f"No se creó el administrador: {error}", file=sys.stderr)
        raise SystemExit(1) from error

    print("Administrador inicial creado.")


if __name__ == "__main__":
    main()