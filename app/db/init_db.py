from app.db.session import engine 
from app.db.base_class import Base 
from app.models.user import User
from app.models.student import StudentProfile
from app.models.company import CompanyProfile

Base.metadata.create_all(bind=engine)