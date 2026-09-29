from app.db.session import engine 
from app.db.base_class import Base 
from app.models.user import User
from app.models.student import StudentProfile
from app.models.company import CompanyProfile
from app.models.application import Application

Base.metadata.create_all(bind=engine)