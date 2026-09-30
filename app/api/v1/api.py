from fastapi import APIRouter
from app.api.v1.endpoints import applications, auth, fct_logs, offers, stats, users



api_router = APIRouter()

api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(offers.router, prefix="/offers", tags=["offers"])
api_router.include_router(applications.router, prefix="/applications", tags=["applications"])
api_router.include_router(fct_logs.router, prefix="/fct-logs", tags=["fct-logs"])
api_router.include_router(stats.router, prefix="/stats", tags=["stats"])