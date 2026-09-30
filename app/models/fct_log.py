from datetime import date
from sqlalchemy import Boolean, Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class FCTLog(Base):
    __tablename__ = "fct_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    hours: Mapped[float] = mapped_column(Float, nullable=False)
    tasks: Mapped[str] = mapped_column(String(250), nullable=False)
    is_approved: Mapped[bool] = mapped_column(default=False)