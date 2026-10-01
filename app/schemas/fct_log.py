from datetime import date

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

class FCTLogBase(BaseModel):
    application_id: int = Field(gt=0)
    date: date
    hours: float = Field(gt=0, le=24)
    tasks: str = Field(min_length=1, max_length=250)

    @field_validator("tasks")
    @classmethod
    def tasks_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("La descripción de tareas no puede estar vacía.")
        return value

    @field_validator("date")
    @classmethod
    def date_must_not_be_in_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("La fecha del registro no puede ser futura.")
        return value

class FCTLogCreate(FCTLogBase):
    pass
    
class FCTLogResponse(BaseModel):
    id: int
    is_approved: bool
    is_tutor_approved: bool

    @computed_field
    @property
    def fully_approved(self) -> bool:
        return self.is_approved and self.is_tutor_approved

    model_config = ConfigDict(from_attributes=True)


