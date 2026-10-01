from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):

    email: EmailStr
    password: str
    role: str = "alumno"

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None

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