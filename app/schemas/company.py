from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class CompanyProfileUpdate(BaseModel):
    company_name: str = Field(min_length=2, max_length=100)
    cif: str = Field(pattern=r"^[ABCDEFGHJNPQRSUVW]\d{7}[0-9A-J]$", max_length=20)
    website: HttpUrl | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("company_name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El campo no puede estar vacío.")
        return value

    @field_validator("cif", mode="before")
    @classmethod
    def normalize_cif(cls, value: str) -> str:
        return value.strip().upper() if isinstance(value, str) else value


class CompanyProfileResponse(BaseModel):
    company_name: str
    cif: str
    website: HttpUrl | None = None

    model_config = ConfigDict(from_attributes=True)