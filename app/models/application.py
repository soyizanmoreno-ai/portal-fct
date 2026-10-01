from datetime import datetime 
from sqlalchemy import func, ForeignKey, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base

class Application(Base):

    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True, index = True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable= False)
    offer_id: Mapped[int] = mapped_column(ForeignKey("offers.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    student: Mapped["User"] = relationship("User")

    status: Mapped[str] = mapped_column(String, default="pendiente")
    feedback: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    student: Mapped["User"] = relationship("User")
    offer: Mapped["Offer"] = relationship("Offer")