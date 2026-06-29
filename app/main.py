from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings
from app.core.logger import logger

logger.info("Iniciando JARVIS-OS...")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Intelligent Personal AI Assistant",
)

app.include_router(api_router)