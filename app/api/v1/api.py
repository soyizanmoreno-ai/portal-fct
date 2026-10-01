# app/api/v1/api.py
from fastapi import APIRouter
from app.api.v1.endpoints import (
    admin, auth, users, offers, applications, fct_logs, stats, tutor, notifications
)

api_router = APIRouter()
api_router.include_router(admin.router, prefix="/admin", tags=["Administración"])
api_router.include_router(auth.router, prefix="/auth", tags=["Autenticación"])
api_router.include_router(users.router, prefix="/users", tags=["Usuarios / Perfil"])
api_router.include_router(offers.router, prefix="/offers", tags=["Ofertas"])
api_router.include_router(applications.router, prefix="/applications", tags=["Candidaturas"])
api_router.include_router(fct_logs.router, prefix="/fct-logs", tags=["Diario FCT"])
api_router.include_router(stats.router, prefix="/stats", tags=["Estadísticas"])
api_router.include_router(tutor.router, prefix="/tutor", tags=["Tutor Centro"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notificaciones"])