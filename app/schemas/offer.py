from pydantic import BaseModel, ConfigDict, Field, model_validator

class OfferBase(BaseModel):
    title: str = Field(min_length=1, max_length=50)
    description: str = Field(min_length=1, max_length=200)

class OfferCreate(OfferBase):
    pass

class OfferUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=50)
    description: str | None = Field(default=None, min_length=1, max_length=200)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def require_updates(self):
        if not self.model_fields_set or any(
            getattr(self, field) is None for field in self.model_fields_set
        ):
            raise ValueError("Indica al menos un campo no nulo para actualizar.")
        return self

class OfferStatusUpdate(BaseModel):
    is_active: bool

    model_config = ConfigDict(extra="forbid")

class OfferResponse(OfferBase):
    id: int
    is_active: bool 
    company_id: int
    company_name: str | None = None

    model_config = ConfigDict(from_attributes=True)