from fastapi import APIRouter

from backend.app.api.routes.cep import router as cep_router
from backend.app.api.routes.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(cep_router)
