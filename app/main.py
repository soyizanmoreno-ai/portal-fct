from fastapi import FastAPI
from app.api.v1.api import api_router
from app.db.base_class import Base
from app.db.session import engine
from app.models.user import User

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Portal FCT API")

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "¡Bienvenido a la API del Portal FCT!"}
    

