from sqlalchemy.orm import Mapped, mapped_column 
from sqlalchemy import String, ForeignKey
from app.db.base_class import Base 

class CompanyProfile(Base):

    __tablename__ = 'companies'

    id: Mapped[int] = mapped_column(primary_key = True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique = True)
    company_name: Mapped[str] = mapped_column(String(100))
    cif: Mapped[str] = mapped_column(String(20), unique = True, index = True)
    website: Mapped[str | None] = mapped_column(String(255), default = None)