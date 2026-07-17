from fastapi import APIRouter

from app.core.config import settings
from app.core.logger import logger

router = APIRouter()


@router.get("/")
def health():
    logger.info("Health endpoint consultado.")

    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online",
        "message": "Welcome to JARVIS-OS",
    }
