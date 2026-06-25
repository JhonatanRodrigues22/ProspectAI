from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.app.api.router import api_router
from backend.app.core.config import settings

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT / "frontend"

app = FastAPI(
    title=settings.app_name,
    version="0.7.0",
    description="API do ProspectAI com busca geográfica e interface MVP.",
)

app.include_router(api_router, prefix="/api")
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
