from sqlalchemy.orm import Mapped, mapped_column 
from sqlalchemy import String
from app.db.base_class import Base 

class User(Base):

    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique = True, index = True)
    hashed_password: Mapped[str] = mapped_column(String(100))
    role: Mapped[str]  = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(default = True)
