from pydantic import BaseModel, EmailStr, ConfigDict, Field, model_validator
from typing import Literal, Optional


class UserCreate(BaseModel):

    email: EmailStr
    password: str = Field(min_length=12)

    model_config = ConfigDict(extra="forbid")

class AdminUserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12)
    role: Literal["alumno", "empresa", "tutor"]

    model_config = ConfigDict(extra="forbid")

class TechnologyEvidence(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    context: Optional[str] = Field(default=None, max_length=300)

    model_config = ConfigDict(extra="forbid")

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, max_length=100)
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    technologies: Optional[list[TechnologyEvidence]] = Field(default=None, max_length=40)
    location_city: Optional[str] = Field(default=None, max_length=100)
    location_province: Optional[str] = Field(default=None, max_length=100)
    education: Optional[list[str]] = Field(default=None, max_length=20)
    experience_projects: Optional[list[str]] = Field(default=None, max_length=20)
    availability: Optional[str] = Field(default=None, max_length=200)
    languages: Optional[list[str]] = Field(default=None, max_length=20)
    soft_skills: Optional[list[str]] = Field(default=None, max_length=30)
    confirm_profile: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def reject_empty_or_null_lists(self):
        if not self.model_fields_set:
            raise ValueError("Indica al menos un cambio o confirma el perfil.")
        list_fields = {
            "technologies", "education", "experience_projects", "languages", "soft_skills"
        }
        if any(getattr(self, field) is None for field in self.model_fields_set & list_fields):
            raise ValueError("Para vaciar una lista, envíala vacía en lugar de null.")
        return self

class UserResponse(BaseModel):

    id: int
    email: EmailStr
    role: str
    is_active: bool = True
    full_name: Optional[str] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    cv_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class StudentProfileFields(BaseModel):
    full_name: Optional[str] = None
    cv_url: Optional[str] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    technologies: list[TechnologyEvidence] = Field(default_factory=list)
    location_city: Optional[str] = None
    location_province: Optional[str] = None
    education: list[str] = Field(default_factory=list)
    experience_projects: list[str] = Field(default_factory=list)
    availability: Optional[str] = None
    languages: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    profile_confirmed: bool = False

    model_config = ConfigDict(from_attributes=True)

class StudentProfileResponse(StudentProfileFields):
    id: int
    email: EmailStr
    role: str
    is_active: bool = True
    suggested_technologies: list[TechnologyEvidence] = Field(default_factory=list)

class StudentCandidateResponse(StudentProfileFields):
    id: int
    email: Optional[EmailStr] = None