from sqlalchemy import ForeignKey, Text, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pydantic import BaseModel, ConfigDict
from app.db.base_class import Base
from app.models.user import User

class Offer(Base):

    __tablename__="offers"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    company: Mapped["User"] = relationship(back_populates="offers")

