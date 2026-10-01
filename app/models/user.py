from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String
from app.db.base_class import Base 

class User(Base):

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique = True, index = True)
    hashed_password: Mapped[str] = mapped_column(String(100))
    role: Mapped[str]  = mapped_column(String(100), default="alumno")
    is_active: Mapped[bool] = mapped_column(default = True)
    offers: Mapped[list["Offer"]] = relationship(back_populates="company")

    github_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    linkedin_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    portfolio_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    cv_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    tutor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    students: Mapped[List["User"]] = relationship("User", remote_side=[tutor_id], backref="tutor")