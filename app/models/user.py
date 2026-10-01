from typing import Optional, List
from sqlalchemy import JSON, String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base
class User(Base):

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique = True, index = True)
    hashed_password: Mapped[str] = mapped_column(String(100))
    role: Mapped[str]  = mapped_column(String(100), default="alumno")
    is_active: Mapped[bool] = mapped_column(default = True)
    full_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    offers: Mapped[list["Offer"]] = relationship(back_populates="company")
    company_profile: Mapped[Optional["CompanyProfile"]] = relationship(
        back_populates="user", uselist=False
    )

    technologies: Mapped[list[dict[str, str | None]]] = mapped_column(JSON, default=list, nullable=False)
    suggested_technologies: Mapped[list[dict[str, str | None]]] = mapped_column(JSON, default=list, nullable=False)
    location_city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location_province: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    education: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    experience_projects: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    availability: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    languages: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    soft_skills: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    profile_confirmed: Mapped[bool] = mapped_column(default=False, nullable=False)

    github_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    linkedin_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    portfolio_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    cv_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    tutor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    tutor: Mapped[Optional["User"]] = relationship(
        "User", remote_side=[id], back_populates="students"
    )
    students: Mapped[List["User"]] = relationship("User", back_populates="tutor")