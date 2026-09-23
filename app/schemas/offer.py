from sqlalchemy import ForeignKey, Text, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pydantic import BaseModel, ConfigDict
from app.db.base_class import Base
from app.models.user import User

class OfferBase(BaseModel):
    title: str
    description: str

class OfferCreate(OfferBase):
    pass

class OfferResponse(OfferBase):
    id: int
    is_active: bool 
    company_id: int

    model_config = ConfigDict(from_attributes=True)