from sqlalchemy.orm import Mapped, mapped_column 
from sqlalchemy import String, ForeignKey
from app.db.base_class import Base 

class StudentProfile(Base):

    __tablename__ = 'students'

    id: Mapped[int] = mapped_column(primary_key = True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique = True)
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))
    cycle: Mapped[str] = mapped_column(String(10))
    cv_url: Mapped[str | None] = mapped_column(String(255))
    github_url: Mapped[str | None] = mapped_column(String(255))
